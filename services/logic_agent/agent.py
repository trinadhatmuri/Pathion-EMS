import time
import mmap
import posix_ipc
import struct
from pymodbus.client import ModbusTcpClient
from config import MODBUS_IP, MODBUS_PORT, SHM_NAME

def run_agent():
    print("--- [AGENT] Smart Energy Management Online ---")
    
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except Exception as e:
        print(f"CRITICAL: SHM Connection Failed: {e}")
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
                print(f"\n🔋 [SAFETY] Battery Full. Turning Solar Switch OFF.")
                if client.connect():
                    client.write_register(3, 0, slave=1) # Write to Reg 3
                    client.close()

            # 2. RECOVERY: Battery Low? Turn Switch (Reg 3) ON
            elif batt < 80 and solar_state == 0:
                print(f"\n☀️ [RECOVERY] Battery {batt}%. Turning Solar Switch ON.")
                if client.connect():
                    client.write_register(3, 1, slave=1) # Write to Reg 3
                    client.close()

            status = "ENABLED" if solar_state == 1 else "DISABLED"
            print(f"AGENT: Batt {batt}% | Switch: {status} | Gen: {solar_kw}kW | Load {load}kW   ", end="\r")

        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
if __name__ == "__main__":
    run_agent()