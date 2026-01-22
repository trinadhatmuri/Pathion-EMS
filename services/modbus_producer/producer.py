import time, mmap, posix_ipc, struct
from pymodbus.client import ModbusTcpClient
from config import MODBUS_IP, MODBUS_PORT, SHM_NAME, SHM_SIZE

def run_producer():
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except:
        shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=SHM_SIZE)
        map_file = mmap.mmap(shm.fd, shm.size)

    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    print(f"--- [PRODUCER] Connecting to {MODBUS_IP}:{MODBUS_PORT} ---")

    while True:
        if client.connect():
            # Read 5 registers (0,1,2,3,4)
            # Due to the offset, we will receive data from indices 1,2,3,4,5
            result = client.read_holding_registers(0, 5, slave=1)
            
            if hasattr(result, 'registers') and len(result.registers) >= 4:
                regs = result.registers
                
                # MAGIC ALIGNMENT:
                # regs[0] is what the Emulator calls Index 1 (Batt)
                batt = regs[0]       
                solar_kw = regs[1]   
                load_kw = regs[2]    
                solar_state = regs[3] 
                
                pulse = int(time.time()) % 65535
                data = struct.pack('>7H', pulse, batt, solar_state, load_kw, solar_kw, 0, 0)
                map_file.seek(0)
                map_file.write(data)
                
                print(f"PRODUCER: Batt {batt}% | Solar {solar_kw}kW | Load {load_kw}kW | Switch {solar_state}   ", end="\r")
        
        time.sleep(1)

if __name__ == "__main__":
    run_producer()