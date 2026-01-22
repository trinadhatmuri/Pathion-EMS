import streamlit as st
import mmap
import posix_ipc
import struct
import time
import pandas as pd
from config import SHM_NAME

st.set_page_config(page_title="EMS Live Monitor", layout="wide")
st.title("🔋 Pathion EMS Control Center")

# Create 4 columns for our new metrics
col1, col2, col3, col4 = st.columns(4)
met_batt = col1.empty()
met_solar = col2.empty()
met_load = col3.empty()
met_status = col4.empty()

# Graph for history
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Battery', 'Solar', 'Load'])

chart_place = st.empty()

try:
    shm = posix_ipc.SharedMemory(SHM_NAME)
    map_file = mmap.mmap(shm.fd, shm.size)
except Exception as e:
    st.error(f"Waiting for Shared Memory... {e}")
    st.stop()

while True:
    try:
        map_file.seek(0)
        # Read the 14 bytes (Pulse, Batt, Switch, Load, Gen, ...)
        data = struct.unpack('>7H', map_file.read(14))
        pulse, batt, switch, load, gen = data[0], data[1], data[2], data[3], data[4]

        # Update Metrics
        met_batt.metric("Battery Storage", f"{batt}%")
        met_solar.metric("Solar Generation", f"{gen} kW")
        met_load.metric("House Load", f"{load} kW")
        
        status_text = "🟢 ONLINE" if switch > 0 else "🔴 OFF (Safety)"
        met_status.metric("Grid Status", status_text)

        # Update Chart (We now graph all 3 to see the interaction!)
        new_entry = pd.DataFrame([[
            time.strftime("%H:%M:%S"), batt, gen, load
        ]], columns=['Time', 'Battery', 'Solar', 'Load'])
        
        # Keep last 50 data points for a smooth scrolling graph
        st.session_state.history = pd.concat([st.session_state.history, new_entry]).tail(50)
        
        # Draw the multiline chart
        chart_place.line_chart(st.session_state.history.set_index('Time'))

    except Exception:
        pass

    time.sleep(1)
    st.rerun()