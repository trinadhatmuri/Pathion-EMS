import time
import mmap
import posix_ipc
import struct
from pymodbus.client import ModbusTcpClient

def log_event(event_type, message):
    log_file = "logs/events.csv"
    os.makedirs("logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, event_type, message])

# Import our central configuration
try:
    from config import (
        MODBUS_IP, MODBUS_PORT, SHM_NAME, 
        BATTERY_MIN, BATTERY_MAX, SOLAR_MAX, 
        WINDOW_SIZE, QUALITY_DANGER, QUALITY_WARNING
    )
except ImportError:
    print("⚠️  Config not found via module path. Ensure you run with -m.")
    exit(1)

def run_agent():
    print(f"--- [AGENT START] Monitoring & Control Active ---")
    
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except Exception as e:
        print(f"CRITICAL: Shared Memory connection failed: {e}")
        return

    last_pulse = -1
    quality_window = [1] * WINDOW_SIZE 

    try:
        while True:
            # 1. SENSE (Read-Only from SHM)
            map_file.seek(0)
            raw_data = map_file.read(12)
            data = struct.unpack('>6H', raw_data)
            
            pulse, battery, solar = data[0], data[1], data[2]

            # 2. EVALUATE (Quality & Sanity)
            if pulse == last_pulse:
                quality_window.append(0)
            else:
                quality_window.append(1)
            
            quality_window.pop(0)
            current_quality = round((sum(quality_window) / WINDOW_SIZE) * 100)
            last_pulse = pulse

            status_icon = "✅ HEALTHY"
            if current_quality < QUALITY_DANGER:
                status_icon = "🚨 CRITICAL"
            elif current_quality < QUALITY_WARNING:
                status_icon = "⚠️  DEGRADED"

            # We add this print to see exactly what the Agent is thinking
            if battery >= 100:
                print(f"\n[CHECK] Batt:{battery} | Solar:{solar} | Quality:{current_quality}% | Required:{QUALITY_WARNING}%")

            # 3. ACT (Control Logic)
            # Check: Is battery full? Is solar on? Is the connection reliable?
            if battery >= 100 and solar > 0 and current_quality >= QUALITY_WARNING:
                log_event("SAFETY_THROTTLE", f"Battery {battery}%, Solar throttled to 0kW")
                print(f"🔋 [SAFETY ACTUATED] Throttling Solar to 0kW...")
                
                try:
                    # Connect directly to hardware
                    with ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT, timeout=2) as ctrl_client:
                        if ctrl_client.connect():
                            # Write 0 to Address 1 (Solar)
                            ctrl_client.write_register(1, 0)
                            print("⚡ Command Successful: Solar Throttled.")
                        else:
                            print("❌ Command Failed: Could not connect to Hardware.")
                except Exception as e:
                    print(f"❌ Control Error: {e}")

            # Dashboard Display
            print(f"{status_icon} | Q: {current_quality:.0f}% | Pulse: {pulse} | Batt: {battery}% | Solar: {solar}kW      ", end="\r")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nAgent shutting down...")
    finally:
        map_file.close()
        shm.close_fd()

if __name__ == "__main__":
    run_agent()