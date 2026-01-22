import threading
import time
import logging
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# Enable internal Modbus logging to see incoming connections
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def battery_physics(block):
    print("--- [PHYSICS ENGINE ONLINE] ---")
    while True:
        # Read from the block (we'll check index 0 and 1)
        vals = block.getValues(0, 3) 
        # We'll take the max of the first two slots to be safe
        current_battery = max(vals[0], vals[1]) 
        current_solar = vals[2] # Solar at index 2
        
        new_battery = current_battery
        if current_solar > 0 and current_battery < 100:
            new_battery += 1
        elif current_solar == 0 and current_battery > 0:
            new_battery -= 1

        if new_battery != current_battery:
            # WRITE TO BOTH INDEX 0 AND 1 TO DEFEAT THE OFFSET BUG
            block.setValues(0, [new_battery, new_battery])
            print(f"DEBUG: Physics Sync -> Batt: {new_battery}%", end="\r")
        
        time.sleep(1)

def run_emulator():
    # Index 0: Batt, Index 1: Batt(Mirror), Index 2: Solar
    initial_values = [50, 50, 0, 0, 0, 0]
    block = ModbusSequentialDataBlock(0, initial_values)
    
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves={1: store}, single=False)
    
    threading.Thread(target=battery_physics, args=(block,), daemon=True).start()
    print("--- [EMULATOR] SYNC MODE: Indices 0 & 1 Mirrored ---")
    StartTcpServer(context=context, address=("0.0.0.0", 502))

if __name__ == "__main__":
    run_emulator()