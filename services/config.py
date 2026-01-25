import os

# --- NETWORK SETTINGS ---
# "os.getenv" looks for a Docker variable first. 
# If not found, it defaults to "127.0.0.1" (Localhost).
MODBUS_IP = os.getenv("MODBUS_IP", "127.0.0.1")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", 5020))

# --- SHARED MEMORY ---
SHM_NAME = "/ems_shared_memory"
SHM_SIZE = 1024

# --- DATA MAPPING ---
# Index 0: Heartbeat/Pulse
# Index 1: Battery %
# Index 2: Switch Status (0=Off, 1=On)
# Index 3: Load kW
# Index 4: Solar kW

# --- SAFETY & LOGIC THRESHOLDS ---
BATTERY_MIN = 0
BATTERY_MAX = 100
SOLAR_MAX = 5000  # kW
STALE_THRESHOLD = 5 # seconds

# --- QUALITY SETTINGS ---
WINDOW_SIZE = 10 # Check the last 10 seconds
QUALITY_DANGER = 60 # Below 60% is Red
QUALITY_WARNING = 90 # Below 90% is Yellow

# --- ALARM SETTINGS ---
DEBOUNCE_LIMIT = 3 # Seconds to wait before confirming a safety trip