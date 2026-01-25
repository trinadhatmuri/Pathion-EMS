import sys
import os

# Fix import path so we can find 'logic_agent' and 'config'
sys.path.append(os.getcwd())

from logic_agent.analysis import SystemAnalyzer

def run_test():
    print("--- 🧪 STARTING LOGIC UNIT TEST ---")
    brain = SystemAnalyzer()

    # TEST SCENARIO 1: Normal Operation
    # Expectation: Quiet. No alarms.
    print("\n[Scenario 1] Normal Operation (Battery 50% -> 52%)")
    print(f"Input: 50% | Output: {brain.evaluate(50, 1)}")
    print(f"Input: 51% | Output: {brain.evaluate(51, 1)}")
    print(f"Input: 52% | Output: {brain.evaluate(52, 1)}")

    # TEST SCENARIO 2: Debounce Check (The Config Test)
    # Expectation: No action for first 2 seconds. ACTION on 3rd.
    print(f"\n[Scenario 2] Overcharge Debounce (Threshold: 3 seconds)")
    
    # Sec 1 (Counter = 1) -> None
    res1 = brain.evaluate(100, 1) 
    print(f"Sec 1 (100%): {res1}") 
    assert res1 is None, "❌ Failed! It acted too early."

    # Sec 2 (Counter = 2) -> None
    res2 = brain.evaluate(100, 1)
    print(f"Sec 2 (100%): {res2}")
    assert res2 is None, "❌ Failed! It acted too early."

    # Sec 3 (Counter = 3) -> DISCONNECT!
    res3 = brain.evaluate(100, 1)
    print(f"Sec 3 (100%): {res3['action'] if res3 else 'None'}")
    assert res3 is not None and res3['action'] == "DISCONNECT_SOLAR", "❌ Failed! It did not trip."
    
    print("✅ DEBOUNCE LOGIC PASSED")

    # TEST SCENARIO 3: Sudden Drop (Rate of Change)
    # Expectation: CRITICAL ALARM immediately.
    print("\n[Scenario 3] Catastrophic Drop (100% -> 90%)")
    res_drop = brain.evaluate(90, 0) # Dropped 10% in 1 step
    print(f"Drop Output: {res_drop}")
    
    assert res_drop is not None and res_drop['severity'] == "CRITICAL", "❌ Failed! No Critical Alarm."
    print("✅ RATE-OF-CHANGE LOGIC PASSED")

if __name__ == "__main__":
    run_test()