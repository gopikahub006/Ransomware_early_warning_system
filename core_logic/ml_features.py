from collections import Counter
from math import log2

# -------------------------
# Entropy function
# -------------------------
def compute_entropy(event_counts):
    total = sum(event_counts.values())
    if total == 0:
        return 0
    return -sum((c / total) * log2(c / total) for c in event_counts.values() if c > 0)

# -------------------------
# Feature extraction function
# -------------------------
def extract_features(events, window_seconds=10):
    """
    events: list of dicts with 'type' and 'timestamp', e.g.,
        [{'type':'CREATE','timestamp':0.1}, {'type':'DELETE','timestamp':1.2}, ...]
    window_seconds: size of time window to compute features
    returns: list of feature vectors [[features_for_window1], [features_for_window2], ...]
    """
    feature_vectors = []
    if not events:
        return feature_vectors

    # Sort events by timestamp
    events = sorted(events, key=lambda x: x['timestamp'])
    start_time = events[0]['timestamp']
    end_time = start_time + window_seconds
    window_events = []

    for event in events:
        ts = event['timestamp']
        # If event falls into current window
        if ts <= end_time:
            window_events.append(event)
        else:
            # Process current window
            feature_vectors.append(process_window(window_events, window_seconds))
            # Start next window
            window_events = [event]
            start_time = end_time
            end_time = start_time + window_seconds

    # Process last window
    if window_events:
        feature_vectors.append(process_window(window_events, window_seconds))

    return feature_vectors

# -------------------------
# Process a single window
# -------------------------
def process_window(window_events, window_seconds):
    total_events = len(window_events)
    event_types = [e['type'] for e in window_events]
    counts = Counter(event_types)

    modify_count = counts.get('MODIFY', 0)
    rename_count = counts.get('RENAME', 0)
    delete_count = counts.get('DELETE', 0)
    delete_ratio = delete_count / total_events if total_events > 0 else 0
    op_entropy = compute_entropy(counts)
    burstiness = total_events / window_seconds

    return [modify_count, rename_count, delete_ratio, op_entropy, burstiness]
if __name__ == "__main__":
    # test the feature extraction
    events = [
        {'type':'CREATE','timestamp':0.5},
        {'type':'MODIFY','timestamp':1.2},
        {'type':'RENAME','timestamp':2.5},
        {'type':'DELETE','timestamp':3.0},
        {'type':'MODIFY','timestamp':5.5},
        {'type':'DELETE','timestamp':9.0},
    ]
    features = extract_features(events, window_seconds=10)
    print(features)

