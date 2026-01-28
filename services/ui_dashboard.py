import streamlit as st
import pandas as pd
import time
import requests

# --- CONFIGURATION ---
API_URL = "http://api:8000"

st.set_page_config(page_title="EMS Live Dashboard", layout="wide")
st.title("⚡ EMS Industrial Dashboard")

# --- HELPER FUNCTIONS ---
def fetch_data():
    try:
        response = requests.get(f"{API_URL}/history", timeout=2)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def fetch_status():
    try:
        response = requests.get(f"{API_URL}/status", timeout=1)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def send_command(action):
    try:
        requests.post(f"{API_URL}/control", json={"action": action})
        st.toast(f"✅ Command Sent: {action}", icon="🚀")
    except Exception as e:
        st.error(f"Failed to send command: {e}")

# --- 1. SIDEBAR ---
with st.sidebar:
    st.header("🎮 Mission Control")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 FORCE ON", use_container_width=True):
            send_command("ON")
    with col2:
        if st.button("🔴 FORCE OFF", use_container_width=True):
            send_command("OFF")
    st.divider()
    st.caption("System refreshes every 1s")

# --- 2. MAIN DASHBOARD ---
status = fetch_status()
df = fetch_data()

if status:
    # --- A. VISUAL BATTERY SECTION ---
    batt_level = status.get('battery_level_pct', 0)
    
    if batt_level > 50:
        health_color = "green"
        health_msg = "✅ HEALTHY"
    elif batt_level > 20:
        health_color = "orange"
        health_msg = "⚠️ LOW"
    else:
        health_color = "red"
        health_msg = "🛑 CRITICAL"

    st.subheader("🔋 Energy Storage System")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.progress(batt_level / 100, text=f"Charge Level: {batt_level}%")
    with c2:
        st.markdown(f"**Status:** :{health_color}[{health_msg}]")

    st.divider()

    # --- B. LIVE METRICS ---
    m1, m2, m3 = st.columns(3)
    
    solar_kw = status.get('solar_generation_kw', 0)
    m1.metric("☀️ Solar Input", f"{solar_kw} kW", delta="Active" if solar_kw > 0 else "Offline")
    
    load_kw = status.get('grid_load_kw', 0)
    m2.metric("🏠 House Load", f"{load_kw} kW", delta_color="inverse")
    
    last_cmd = status.get('reserved_1', 0)
    cmd_text = "AUTO"
    if last_cmd == 1: cmd_text = "MANUAL: ON"
    if last_cmd == 2: cmd_text = "MANUAL: OFF"
    m3.metric("⚙️ Control Mode", cmd_text)

else:
    st.warning("⚠️ Connecting to System...")

# --- C. SEPARATE CHARTS SECTION ---
if not df.empty:
    if "Timestamp" in df.columns:
        df = df.set_index("Timestamp")

    st.markdown("### 📊 Historical Analysis")

    # 1. Battery History (Full Width Area Chart)
    st.caption("Energy Storage Trend (Last 100 Ticks)")
    # We rename it so the legend looks clean
    st.area_chart(df[["Battery_Pct"]].rename(columns={"Battery_Pct": "Battery %"}), color="#4CAF50") # Green

    # 2. Split Charts for Solar and Load
    col_solar, col_load = st.columns(2)

    with col_solar:
        st.caption("☀️ Solar Production (kW)")
        st.area_chart(df[["Gen_kW"]].rename(columns={"Gen_kW": "Solar Output"}), color="#FFC107") # Gold/Yellow

    with col_load:
        st.caption("🏠 House Consumption (kW)")
        st.line_chart(df[["Load_kW"]].rename(columns={"Load_kW": "Load"}), color="#F44336") # Red

# --- 3. REFRESH ---
time.sleep(1)
st.rerun()