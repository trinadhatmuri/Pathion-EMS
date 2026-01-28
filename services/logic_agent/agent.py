import time
import mmap
import posix_ipc
import struct
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from config import MODBUS_IP, MODBUS_PORT, SHM_NAME

# Import your new Brain
from logic_agent.analysis import SystemAnalyzer

# --- LOGGING SETUP ---
LOG_DIR = "data/logs"
EVENT_LOG_PATH = os.path.join(LOG_DIR, "events.log")

def log_event(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {message}"
    print(f"\n{formatted_msg}")
    try:
        with open(EVENT_LOG_PATH, "a") as f:
            f.write(formatted_msg + "\n")
    except Exception:
        pass

def run_agent():
    print("--- [AGENT] Industrial Controller Online ---")
    log_event("INFO", "System Initialized.")
    
    # 1. Initialize the Brain
    analyzer = SystemAnalyzer()
    
    # 2. Connect to Hardware
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except Exception as e:
        log_event("CRITICAL", f"SHM Failure: {e}")
        return

    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)

    while True:
        try:
            map_file.seek(0)
            data = struct.unpack('>7H', map_file.read(14))
            pulse, batt, solar_state, load, solar_kw, manual_command = data[0], data[1], data[2], data[3], data[4], data[5]
            
            if manual_command > 0:
                log_event("WARNING", f"Received Manual Override Command: {manual_command}")
                
                # Execute immediately
                if client.connect():
                    if manual_command == 1: # FORCE ON
                        client.write_register(3, 1, slave=1)
                        log_event("INFO", "Manual Action: Solar CONNECTED")
                    elif manual_command == 2: # FORCE OFF
                        client.write_register(3, 0, slave=1)
                        log_event("INFO", "Manual Action: Solar DISCONNECTED")
                    client.close()
                
                # CRITICAL: Clear the mailbox so we don't execute it forever!
                # Offset for Index 5 = 10 bytes (5 * 2 bytes)
                map_file.seek(10)
                map_file.write(struct.pack('>H', 0)) # Write a single 0 to Index 5
                
                # Skip the brain this cycle (Human overrules AI)
                time.sleep(1)
                continue
            
            # --- ASK THE BRAIN ---
            result = analyzer.evaluate(batt, solar_state)
            
            # --- EXECUTE DECISION ---
            if result:
                log_event(result['severity'], result['reason'])
                
                if result['action'] == "DISCONNECT_SOLAR":
                    if client.connect():
                        client.write_register(3, 0, slave=1)
                        client.close()
                        
                elif result['action'] == "RECONNECT_SOLAR":
                    if client.connect():
                        client.write_register(3, 1, slave=1)
                        client.close()

            # Status Update
            status = "ON" if solar_state == 1 else "OFF"
            print(f"AGENT: Batt {batt}% | Switch: {status} | Gen: {solar_kw}kW | Load {load}kW   ", end="\r")

        except Exception as e:
            log_event("ERROR", f"Loop Exception: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    run_agent()