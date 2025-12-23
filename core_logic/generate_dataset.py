import random
import pickle
from core_logic.ml_features import extract_features

# -------------------------
# Configuration
# -------------------------
NUM_SEQUENCES = 200       # number of sequences per class
EVENTS_PER_SEQUENCE = 50  # events per sequence
WINDOW_SECONDS = 10

# -------------------------
# Generate NORMAL sequences
# -------------------------
normal_sequences_all = []

for _ in range(NUM_SEQUENCES):
    ts = 0
    sequence = []
    for _ in range(EVENTS_PER_SEQUENCE):
        ts += random.uniform(0.5, 2.0)  # slower user actions
        event_type = random.choice(['CREATE', 'MODIFY'])
        sequence.append({'type': event_type, 'timestamp': ts})
    normal_sequences_all.append(sequence)

# -------------------------
# Generate MALICIOUS sequences
# -------------------------
malicious_sequences_all = []

for _ in range(NUM_SEQUENCES):
    ts = 0
    sequence = []
    for _ in range(EVENTS_PER_SEQUENCE):
        ts += random.uniform(0.05, 0.3)  # rapid file operations
        event_type = random.choice(['MODIFY', 'RENAME', 'DELETE'])
        sequence.append({'type': event_type, 'timestamp': ts})
    malicious_sequences_all.append(sequence)

# -------------------------
# Extract features
# -------------------------
X, y = [], []

# NORMAL → 0
for seq in normal_sequences_all:
    for f in extract_features(seq, WINDOW_SECONDS):
        X.append(f)
        y.append(0)

# MALICIOUS → 1
for seq in malicious_sequences_all:
    for f in extract_features(seq, WINDOW_SECONDS):
        X.append(f)
        y.append(1)

# -------------------------
# Save dataset
# -------------------------
with open("core_logic/ml_dataset.pkl", "wb") as f:
    pickle.dump({"X": X, "y": y}, f)

print(f"[SUCCESS] Dataset created with {len(X)} samples")
