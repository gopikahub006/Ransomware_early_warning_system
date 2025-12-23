import time
import random
import threading

RISK_SCORES = {
    "Encrypting_Operation": 50,
    "Delete_Backups": 75,
    "File_Rename_Op": 25,
    "Mass_File_Read": 10,
    "Normal_Modify": 2,
    "Normal_Access": 1
}

class EventSimulator(threading.Thread):
    def __init__(self, mode="NORMAL", event_queue=None):
        super().__init__(daemon=True)
        self.mode = mode
        self.event_queue = event_queue
        self.running = True

    def run(self):
        while self.running:
            if self.mode == "NORMAL":
                action = random.choice(
                    ["Normal_Access", "Normal_Modify"]
                )
                delay = random.uniform(0.8, 1.5)
            else:
                action = random.choice([
                    "Encrypting_Operation",
                    "File_Rename_Op",
                    "Mass_File_Read",
                    "Delete_Backups"
                ])
                delay = random.uniform(0.1, 0.4)

            risk = RISK_SCORES[action]

            event = {
                "timestamp": time.time(),
                "type": action,
                "file": "SimulatedFile",
                "risk": risk
            }

            if self.event_queue:
                self.event_queue.put(event)

            time.sleep(delay)

    def stop(self):
        self.running = False
