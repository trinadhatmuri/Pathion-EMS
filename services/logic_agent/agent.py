import time, mmap, posix_ipc, struct
from pymodbus.client import ModbusTcpClient
from config import *

def run_agent():
    print("--- [AGENT] Monitoring Shared Memory ---")
    shm = posix_ipc.SharedMemory(SHM_NAME)
    map_file = mmap.mmap(shm.fd, shm.size)
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)

    while True:
        map_file.seek(0)
        # Read the 14 bytes (Pulse, Batt, Solar, ...)
        data = struct.unpack('>7H', map_file.read(14))
        pulse, batt, solar = data[0], data[1], data[2]
        
        print(f"AGENT: Read Batt {batt}% | Pulse {pulse}          ", end="\r")

        # Safety Logic
        if batt >= 100 and solar > 0:
            print(f"\n🔋 [SAFETY] Battery Full! Throttling Solar...")
            if client.connect():
                client.write_register(1, 0)
                client.close()
        
        time.sleep(1)

if __name__ == "__main__":
    run_agent()