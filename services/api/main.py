from fastapi import FastAPI, HTTPException
import posix_ipc
import mmap
import struct
import os
import sys
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config import SHM_NAME, SHM_SIZE

app = FastAPI(title="EMS Industrial API", version="1.0")

try:
    shm = posix_ipc.SharedMemory(SHM_NAME)
    map_file = mmap.mmap(shm.fd, shm.size)
except Exception as e:
    logger.critical(f"CRITICAL: API cannot connect to Shared Memory. Is the Emulator running? {e}")
    shm = None
    map_file = None

@app.get("/")
def home():
    """ Health check endpoint """
    return {"status": "online", "system": "Energy Management System"}

@app.get("/status")
def get_status():
    """ Reads directly from RAM (Shared Memory) to get the millisecond-accurate state. """
    if map_file is None:
        raise HTTPException(status_code=503, detail="System Offline (SHM unreachable)")

    # 0: Pulse, 1: Batt, 2: Solar_State, 3: Load, 4: Solar_Gen, 5: Gen_Power, 6: Generator KW
    try:
        map_file.seek(0)
        data_bytes = map_file.read(14)
        data = struct.unpack('>7H', data_bytes)
        
        response = {
            "heartbeat": data[0],
            "battery_level_pct": data[1],
            "switch_state": "ON" if data[2] == 1 else "OFF",
            "grid_load_kw": data[3],
            "solar_generation_kw": data[4],  # <--- This was labeled 'generator' before
            "reserved_1": data[5],           # These are just padding (0) for now
            "reserved_2": data[6]
        }
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading status: {e}")

class ControlCommand(BaseModel):
    action: str  # Solar action: 0 - "No Action" 1 - "ON" or 2 - "OFF"

@app.post("/control")
def send_command(cmd: ControlCommand):
    if map_file is None:
        raise HTTPException(status_code=503, detail="System Offline (SHM unreachable)")

    if cmd.action.upper() == "ON":
            value = 1
    elif cmd.action.upper() == "OFF":
            value = 2
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use ON or OFF")

    COMMAND_OFFSET = 10  # Offset for the Control Register in Shared Memory

    try:
        map_file.seek(COMMAND_OFFSET)
        map_file.write(struct.pack('>H', value))
        return {"status": "Command Sent", "action": cmd.action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))