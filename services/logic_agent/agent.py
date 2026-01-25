import time
import mmap
import posix_ipc
import struct
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from config import MODBUS_IP, MODBUS_PORT, SHM_NAME

# --- ALARM LOGGING SETUP ---
LOG_DIR = "data/logs"
EVENT_LOG_PATH = os.path.join(LOG_DIR, "events.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_event(level, message):
    """
    Logs an alarm event to both the console and a permanent file.
    Format: [TIMESTAMP] [LEVEL] Message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {message}"
    
    # 1. Print to Console (for you to see now)
    print(f"\n{formatted_msg}")
    
    # 2. Append to File (for your boss to see later)
    try:
        with open(EVENT_LOG_PATH, "a") as f:
            f.write(formatted_msg + "\n")
    except Exception as e:
        print(f"Error writing to event log: {e}")

def run_agent():
    print("--- [AGENT] Smart Energy Management Online ---")
    log_event("INFO", "Agent Process Started.")
    
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except Exception as e:
        log_event("CRITICAL", f"SHM Connection Failed: {e}")
        return

    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)

    while True:
        try:
            map_file.seek(0)
            data = struct.unpack('>7H', map_file.read(14))
            # Unpack matches Producer: [Pulse, Batt, State, Load, SolarPower, ...]
            pulse, batt, solar_state, load, solar_kw = data[0], data[1], data[2], data[3], data[4]
            
            # 1. SAFETY: Battery Full? Turn Switch (Reg 3) OFF
            if batt >= 100 and solar_state == 1:
                # Log the Alarm
                log_event("WARNING", f"Battery Full ({batt}%). Safety Threshold Breached. Action: DISCONNECT Solar.")
                
                if client.connect():
                    client.write_register(3, 0, slave=1) # Write to Reg 3
                    client.close()

            # 2. RECOVERY: Battery Low? Turn Switch (Reg 3) ON
            elif batt < 80 and solar_state == 0:
                # Log the Recovery
                log_event("INFO", f"Battery Recovery ({batt}%). Threshold Normal. Action: RECONNECT Solar.")
                
                if client.connect():
                    client.write_register(3, 1, slave=1) # Write to Reg 3
                    client.close()

            status = "ENABLED" if solar_state == 1 else "DISABLED"
            print(f"AGENT: Batt {batt}% | Switch: {status} | Gen: {solar_kw}kW | Load {load}kW   ", end="\r")

        except Exception as e:
            log_event("ERROR", f"Agent Loop Exception: {e}")
        time.sleep(1)

if __name__ == "__main__":
    run_agent()