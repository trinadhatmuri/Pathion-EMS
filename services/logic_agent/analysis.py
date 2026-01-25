from config import DEBOUNCE_LIMIT

class SystemAnalyzer:
    def __init__(self):
        # Memory for Rate-of-Change (RoC)
        self.prev_battery = None
        
        # Memory for Debouncing (Time Delay)
        self.overcharge_counter = 0
        self.DEBOUNCE_LIMIT = 3  # Must stay at 100% for 3 cycles (3 seconds)
        
        # State tracking
        self.safety_tripped = False

    def evaluate(self, current_batt, solar_state):
        """
        Input: Current sensors.
        Output: A decision dictionary { "action": ..., "reason": ..., "severity": ... }
        """
        decision = None

        # --- 1. RATE OF CHANGE (RoC) ANALYSIS ---
        # Detect sudden drops (e.g. short circuit or theft)
        if self.prev_battery is not None:
            drop = self.prev_battery - current_batt
            if drop >= 5:  # Dropped 5% in 1 second!
                return {
                    "action": "ALARM_ONLY",
                    "reason": f"CRITICAL: Sudden Battery Drop detected (-{drop}%/sec)",
                    "severity": "CRITICAL"
                }
        
        # Update history for next second
        self.prev_battery = current_batt

        # --- 2. DEBOUNCED SAFETY TRIP ---
        # Only trip if battery is Full AND Solar is ON
        if current_batt >= 100 and solar_state == 1:
            self.overcharge_counter += 1
            
            # Have we seen this for 3 seconds straight?
            if self.overcharge_counter >= self.DEBOUNCE_LIMIT:
                self.safety_tripped = True
                return {
                    "action": "DISCONNECT_SOLAR",
                    "reason": f"Battery Overcharge Confirmed ({current_batt}%)",
                    "severity": "WARNING"
                }
        else:
            # Reset counter if it dips even for a second (Noise filtering)
            self.overcharge_counter = 0

        # --- 3. HYSTERESIS RECOVERY ---
        # Only recover if we are currently TRIPPED and battery is SAFE
        if self.safety_tripped and current_batt < 80:
            self.safety_tripped = False
            return {
                "action": "RECONNECT_SOLAR",
                "reason": f"Battery Safe ({current_batt}%). Resuming Generation.",
                "severity": "INFO"
            }

        return decision