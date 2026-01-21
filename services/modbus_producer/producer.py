import time
import mmap
import posix_ipc
import struct
import logging
from logging.handlers import TimedRotatingFileHandler
from pymodbus.client import ModbusTcpClient

from config import MODBUS_IP, MODBUS_PORT, SHM_NAME, SHM_SIZE

# 1. SETUP LOGGING
log_file = "logs/producer.log"
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger("Producer")

# 2. CONFIG
SHM_NAME = SHM_NAME
SHM_SIZE = SHM_SIZE
MODBUS_IP = MODBUS_IP
MODBUS_PORT = MODBUS_PORT

def run_producer():
    # Setup Shared Memory
    try:
        # If SHM exists from a previous crash, we try to open it; otherwise create it
        try:
            shm = posix_ipc.SharedMemory(SHM_NAME)
        except posix_ipc.ExistentialError:
            shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=SHM_SIZE)
            
        map_file = mmap.mmap(shm.fd, shm.size)
        logger.info("--- [SUCCESS] Shared Memory Whiteboard is Open ---")
    except Exception as e:
        logger.error(f"Critical Shared Memory Error: {e}")
        return

    # Initialize Modbus Client with a 2-second timeout
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT, timeout=2)

    while True:
        try:
            # Check if we are connected; if not, try to connect
            if not client.connect():
                logger.warning(f"Unable to connect to Emulator at {MODBUS_IP}:{MODBUS_PORT}. Retrying...")
                time.sleep(2)
                continue
            
            # If we reach here, we are connected. Let's read 100 registers.
            # In Pymodbus 3.x, use slave=1 or simply the call below
            result = client.read_holding_registers(0, 100, slave=1)
            
            if not result.isError():
                # Create a Heartbeat (0-65535) to show the data is "Live"
                heartbeat = int(time.time()) % 65535 
                data_to_pack = [heartbeat] + result.registers
                
                # Pack: '>' Big Endian, 'H' Unsigned Short (2 bytes)
                # We pack the heartbeat + the registers we read
                fmt = f'>{len(data_to_pack)}H'
                data_bytes = struct.pack(fmt, *data_to_pack)
                
                # Write to the Start of the Whiteboard (RAM)
                map_file.seek(0)
                map_file.write(data_bytes)
                
                # We don't want to spam the log, so we only log success once every 60 seconds
                if heartbeat % 60 == 0:
                    logger.info(f"Pipeline Healthy. Heartbeat: {heartbeat}")
            else:
                logger.error(f"Modbus Protocol Error: {result}")
                
        except Exception as e:
            logger.error(f"Unexpected Loop Error: {e}")
            # If the network breaks, close the client so we can fresh-connect next loop
            client.close()
            time.sleep(2)
            
        time.sleep(1) # Frequency of "Sensing" is 1Hz (once per second)

if __name__ == "__main__":
    run_producer()