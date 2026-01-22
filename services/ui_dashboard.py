import streamlit as st
import mmap
import posix_ipc
import struct
import time
import pandas as pd
from config import SHM_NAME

st.set_page_config(page_title="EMS Live Monitor", layout="wide")
st.title("🔋 Pathion EMS Control Center")

# Placeholders for live metrics
col1, col2, col3 = st.columns(3)
met_pulse = col1.empty()
met_batt = col2.empty()
met_solar = col3.empty()

# Graph for history
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Battery'])

chart_place = st.empty()

try:
    shm = posix_ipc.SharedMemory(SHM_NAME)
    map_file = mmap.mmap(shm.fd, shm.size)
except Exception as e:
    st.error(f"Waiting for Shared Memory... {e}")
    st.stop()

while True:
    map_file.seek(0)
    # Read the 14 bytes (Pulse, Batt, Solar, etc.)
    data = struct.unpack('>7H', map_file.read(14))
    pulse, batt, solar = data[0], data[1], data[2]

    # Update Metrics
    met_pulse.metric("System Heartbeat", pulse)
    met_batt.metric("Battery Storage", f"{batt}%")
    met_solar.metric("Solar Input", f"{solar} kW")

    # Update Chart
    new_entry = pd.DataFrame([[time.strftime("%H:%M:%S"), batt]], columns=['Time', 'Battery'])
    st.session_state.history = pd.concat([st.session_state.history, new_entry]).tail(20)
    chart_place.line_chart(st.session_state.history.set_index('Time'))

    time.sleep(1)
    st.rerun()