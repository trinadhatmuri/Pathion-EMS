import pandas as pd
import glob
import os

LOG_DIR = "data/logs"
COST_PER_KWH = 0.15  # Average electricity cost ($0.15/kWh)

def generate_report():
    print("--- [EMS] FINANCIAL PERFORMANCE REPORT ---")
    
    # 1. Load all log files
    all_files = glob.glob(f"{LOG_DIR}/*.csv")
    if not all_files:
        print("No data found.")
        return

    df_list = []
    for filename in all_files:
        df = pd.read_csv(filename)
        df_list.append(df)
    
    # Combine into one big timeline
    full_history = pd.concat(df_list)
    
    # 2. Calculate Energy
    # Our data is in "Kilowatts per Second". 
    # To get kWh, we divide the sum by 3600 (seconds in an hour).
    total_samples = len(full_history)
    total_solar_kw_seconds = full_history['Gen_kW'].sum()
    total_load_kw_seconds = full_history['Load_kW'].sum()
    
    total_solar_kwh = total_solar_kw_seconds / 3600
    total_load_kwh = total_load_kw_seconds / 3600
    
    # 3. Calculate Savings
    # Assumption: Every bit of Solar used is energy we didn't buy from the grid.
    savings = total_solar_kwh * COST_PER_KWH
    
    # 4. Print Metrics
    print(f"📊 Total Runtime:    {total_samples} seconds")
    print(f"☀️ Solar Generated:  {total_solar_kwh:.4f} kWh")
    print(f"🏠 House Consumption:{total_load_kwh:.4f} kWh")
    print(f"----------------------------------------")
    print(f"💰 ESTIMATED SAVINGS: ${savings:.4f}")
    print(f"----------------------------------------")
    
    # Deep Cycle Check
    # Count how many times we hit the "bottom" (roughly < 81%)
    deep_cycles = len(full_history[full_history['Battery_Pct'] < 81])
    print(f"🔋 Deep Cycle Events: {deep_cycles} (Seconds spent below 81%)")

if __name__ == "__main__":
    generate_report()