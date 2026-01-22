import time, mmap, posix_ipc, struct
from pymodbus.client import ModbusTcpClient
from config import MODBUS_IP, MODBUS_PORT, SHM_NAME, SHM_SIZE

def run_producer():
    # 1. Clean Slate Shared Memory
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=SHM_SIZE)
        map_file = mmap.mmap(shm.fd, shm.size)
    except:
        # If it exists, open it
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)

    # 2. Connect
    client = ModbusTcpClient("127.0.0.1", port=502)

    print("--- [PRODUCER] Connecting to Unit ID 1... ---")

    while True:
        if not client.connect():
            print("PRODUCER: Connection Refused. Is Emulator Running?")
            time.sleep(2)
            continue

        # 3. EXPLICIT READ: Address 0, Count 2, Slave Unit 1
        # We try-catch to avoid crashing on errors
        try:
            # Read 3 registers to cover the offset
            result = client.read_holding_registers(0, 3, slave=1)
            
            if hasattr(result, 'registers') and result.registers:
                regs = result.registers
                # Logic: If index 0 is 0, the data is likely at index 1 due to the offset
                batt = regs[0] if regs[0] > 0 else regs[1]
                solar = regs[2] # Solar is now at index 2
                
                pulse = int(time.time()) % 65535
                data = struct.pack('>7H', pulse, batt, solar, 0, 0, 0, 0)
                map_file.seek(0)
                map_file.write(data)
                
                print(f"PRODUCER SUCCESS: Read Batt {batt}% | Solar {solar}kW", end="\r")
            else:
                print(f"PRODUCER ERROR: Emulator connected but returned no data. Result: {result}")
                
        except Exception as e:
            print(f"PRODUCER EXCEPTION: {e}")

        time.sleep(1)

if __name__ == "__main__":
    run_producer()