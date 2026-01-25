import time
import mmap
import posix_ipc
import struct
import os
from datetime import datetime
from config import SHM_NAME

# Setup Log Directory
LOG_DIR = "data/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_log_filepath():
    """Generates a filename based on the current hour.
       Example: data/logs/2026-01-25_19.csv
    """
    now = datetime.now()
    # Format: YYYY-MM-DD_HH (Hourly files)
    filename = f"{now.strftime('%Y-%m-%d_%H')}.csv"
    return os.path.join(LOG_DIR, filename)

def run_logger():
    print("--- [LOGD] High-Speed Data Recorder Online ---")
    
    # 1. Connect to Shared Memory
    try:
        shm = posix_ipc.SharedMemory(SHM_NAME)
        map_file = mmap.mmap(shm.fd, shm.size)
    except Exception as e:
        print(f"CRITICAL: Could not connect to Shared Memory. Is Producer running? ({e})")
        return

    current_file_path = None
    file_handle = None

    while True:
        try:
            # 2. Read from Memory (The "Truth")
            map_file.seek(0)
            data_bytes = map_file.read(14)
            
            # Unpack matches our verified map: [Pulse, Batt, Switch, Load, Gen]
            data = struct.unpack('>7H', data_bytes)
            pulse, batt, switch, load, gen = data[0], data[1], data[2], data[3], data[4]
            
            # 3. File Rotation Logic
            target_file_path = get_log_filepath()
            
            # If the hour changed (or we just started), switch files
            if target_file_path != current_file_path:
                if file_handle:
                    file_handle.close()
                    print(f"\n[LOGD] Closed old log: {current_file_path}")
                
                # Open new file in Append mode
                current_file_path = target_file_path
                file_handle = open(current_file_path, "a")
                
                # If it's a new file, add headers
                if os.path.getsize(current_file_path) == 0:
                    file_handle.write("Timestamp,Battery_Pct,Solar_Switch,Load_kW,Gen_kW\n")
                    print(f"[LOGD] Created new log: {current_file_path}")

            # 4. Write the Record
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            csv_line = f"{timestamp},{batt},{switch},{load},{gen}\n"
            
            file_handle.write(csv_line)
            file_handle.flush() # Ensure data hits the disk immediately (Safety)
            
            print(f"LOGD: Saved {timestamp} | Batt {batt}%", end="\r")

        except Exception as e:
            print(f"\n[ERROR]: {e}")
            # Try to reconnect/recover
            time.sleep(2)
            
        time.sleep(1)

if __name__ == "__main__":
    run_logger()