import time
import threading
from collections import deque

# -----------------------------
# Configuration
# -----------------------------
TIME_WINDOW = 60          # Increased to 60 to match your GUI graph window
MAX_RISK_SCORE = 200      # Normalization base

class RiskModel:
    """
    Heuristic risk engine using a cumulative score for graphing 
    and a sliding window for active alerts.
    """

    def __init__(self, decay_window=TIME_WINDOW):
        self.decay_window = decay_window
        self.events = deque()  # Stores (timestamp, cumulative_score)
        self.lock = threading.Lock()
        self.total_accumulated = 0 # Persistent total for the graph line

    def add_event(self, ts, score):
        """Add a new risk event and update the cumulative total."""
        with self.lock:
            self.total_accumulated += score
            # Store the timestamp and the NEW total score at that time
            self.events.append((ts, self.total_accumulated))

    def _cleanup(self):
        """Remove expired events older than the 60s graph window."""
        cutoff = time.time() - self.decay_window
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def current_total(self):
        """
        Return the score gained WITHIN the current window.
        This is what triggers the 'SAFE' vs 'HIGH RISK' status.
        """
        with self.lock:
            self._cleanup()
            if len(self.events) < 2:
                return 0
            # Difference between the latest total and the oldest total in the window
            return self.events[-1][1] - self.events[0][1]

    def normalized_risk(self):
        """Return risk normalized between 0 and 1."""
        total = self.current_total()
        return min(total / MAX_RISK_SCORE, 1.0)

# -----------------------------
# TESTING BLOCK
# -----------------------------
if __name__ == "__main__":
    print("Starting Cumulative RiskModel test...")
    rm = RiskModel(decay_window=10)

    rm.add_event(time.time(), 50)
    print(f"Added 50. Current Window Total: {rm.current_total()}")
    
    time.sleep(2)
    rm.add_event(time.time(), 75)
    print(f"Added 75. Current Window Total: {rm.current_total()}")
    
    print("If you see the total as 125, the graph will now work!")