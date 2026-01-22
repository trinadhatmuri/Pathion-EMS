# ems-project/services/config.py

# Data Mapping (The "Decoder Ring" blueprint)
# Index 0: Heartbeat/Pulse
# Index 1: Battery %
# Index 2: Solar kW

# Network Settings
MODBUS_IP = "127.0.0.1"
MODBUS_PORT = 5020

# Shared Memory Settings
SHM_NAME = "/ems_shared_memory"
SHM_SIZE = 1024

# Safety Thresholds
BATTERY_MIN = 0
BATTERY_MAX = 100
SOLAR_MAX = 5000  # kW
STALE_THRESHOLD = 5 # seconds

# Quality Assessment Settings
WINDOW_SIZE = 10 # Check the last 10 seconds
QUALITY_DANGER = 60 # Below 60% is Red
QUALITY_WARNING = 90 # Below 90% is Yellow

