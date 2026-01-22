import threading
import time
import random
import sys
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from config import MODBUS_IP, MODBUS_PORT

# --- THE CONTRACT (SHIFTED +1) ---
# Index 0 is now unreachable/padding.
ADDR_BATT  = 1
ADDR_SOLAR = 2
ADDR_LOAD  = 3
ADDR_CTRL  = 4

def battery_physics(block):
    print("--- [PHYSICS ENGINE ONLINE] ---")
    solar_base = 15
    
    while True:
        try:
            # Read all 5 registers (0-4) to be safe
            vals = block.getValues(0, 5)
            
            # Use our shifted constants
            current_batt = vals[ADDR_BATT]
            solar_control = vals[ADDR_CTRL]
            
            # 1. Physics Logic
            cloud_factor = random.uniform(0.7, 1.0)
            if solar_control > 0:
                current_solar = int(solar_base * cloud_factor)
            else:
                current_solar = 0
                
            house_load = 2 + random.randint(0, 5)
            net_power = current_solar - house_load
            
            new_batt = current_batt
            if net_power > 0 and current_batt < 100:
                new_batt += 1
            elif net_power < 0 and current_batt > 0:
                new_batt -= 1
            
            # 2. Write Back (Using Shifted Constants)
            block.setValues(ADDR_BATT, [new_batt])
            block.setValues(ADDR_SOLAR, [current_solar])
            block.setValues(ADDR_LOAD, [house_load])
            
            # Print status
            state = "ON" if solar_control > 0 else "OFF"
            print(f"PHY: Batt {new_batt}% | Solar {current_solar}kW | Load {house_load}kW | Switch {state}   ", end="\r")
            
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

def run_emulator():
    # Initialize 20 registers
    # Index 0 is Padding (0). Index 1 is Batt (50). Index 4 is Switch (1).
    # [Pad, Batt, Solar, Load, Switch, ...]
    init_data = [0, 50, 0, 0, 1] + [0]*15
    
    block = ModbusSequentialDataBlock(0, init_data)
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves={1: store}, single=False)
    
    threading.Thread(target=battery_physics, args=(block,), daemon=True).start()
    
    print(f"--- [EMULATOR] OFFSET-CORRECTED MODE ON {MODBUS_IP}:{MODBUS_PORT} ---")
    StartTcpServer(context=context, address=(MODBUS_IP, MODBUS_PORT))

if __name__ == "__main__":
    run_emulator()