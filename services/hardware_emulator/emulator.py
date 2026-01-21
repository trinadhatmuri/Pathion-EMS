from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock

# Pymodbus 3.x re-organized these into the 'datastore' or 'context' sub-modules
try:
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
except ImportError:
    from pymodbus.context import ModbusSlaveContext, ModbusServerContext

def run_emulator():
    # Setup 2,000 Holding Registers (hr)
    # We initialize them all with 0
    block = ModbusSequentialDataBlock(0, [0]*2000)
    
    # Create the data store
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves=store, single=True)
    
    print("--- [SUCCESS] EMS Hardware Emulator is LIVE ---")
    print("Simulating 2,000 registers on port 502...")
    print("Press Ctrl+C to stop.")
    
    # Start the server on all interfaces
    StartTcpServer(context=context, address=("0.0.0.0", 502))

if __name__ == "__main__":
    run_emulator()