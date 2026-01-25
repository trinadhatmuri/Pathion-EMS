import streamlit as st
import mmap
import posix_ipc
import struct
import time
import pandas as pd
import os
import glob
from config import SHM_NAME

st.set_page_config(page_title="EMS Live Monitor", layout="wide")
st.title("🔋 Pathion EMS Control Center")

# --- DATA LOADER FUNCTION ---
def load_recent_history():
    """
    Reads the latest CSV log file from disk to populate the graph.
    This ensures data persists even if you refresh the page.
    """
    log_dir = "data/logs"
    if not os.path.exists(log_dir):
        return pd.DataFrame()
    
    # Find all CSV files and pick the newest one
    list_of_files = glob.glob(f"{log_dir}/*.csv")
    if not list_of_files:
        return pd.DataFrame()
    
    latest_file = max(list_of_files, key=os.path.getctime)
    
    try:
        # Read the file. using tail(100) keeps the UI snappy.
        df = pd.read_csv(latest_file)
        return df.tail(100) 
    except Exception:
        return pd.DataFrame()

# --- UI LAYOUT ---
col1, col2, col3, col4 = st.columns(4)
met_batt = col1.empty()
met_solar = col2.empty()
met_load = col3.empty()
met_status = col4.empty()

st.subheader("System History (Persistent Storage)")
chart_place = st.empty()

# --- SHARED MEMORY CONNECTION ---
try:
    shm = posix_ipc.SharedMemory(SHM_NAME)
    map_file = mmap.mmap(shm.fd, shm.size)
except Exception as e:
    st.error(f"Waiting for Shared Memory... {e}")
    st.stop()

# --- MAIN LOOP ---
while True:
    try:
        # 1. FAST PATH: Read Live Metrics from RAM (Shared Memory)
        map_file.seek(0)
        data = struct.unpack('>7H', map_file.read(14))
        pulse, batt, switch, load, gen = data[0], data[1], data[2], data[3], data[4]

        # Update Metrics
        met_batt.metric("Battery Storage", f"{batt}%")
        met_solar.metric("Solar Generation", f"{gen} kW")
        met_load.metric("House Load", f"{load} kW")
        
        status_text = "🟢 ONLINE" if switch > 0 else "🔴 OFF (Safety)"
        met_status.metric("Grid Status", status_text)

        # 2. SLOW PATH: Read History from Disk (CSV)
        history_df = load_recent_history()
        
        if not history_df.empty:
            # Select specific columns to graph
            # CSV Headers: Timestamp, Battery_Pct, Solar_Switch, Load_kW, Gen_kW
            chart_data = history_df[['Timestamp', 'Battery_Pct', 'Gen_kW', 'Load_kW']].set_index('Timestamp')
            
            # Draw the chart
            chart_place.line_chart(chart_data)

    except Exception:
        pass

    # Refresh every second
    time.sleep(1)
    st.rerun()