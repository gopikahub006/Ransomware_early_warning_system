import pickle
from sklearn.ensemble import RandomForestClassifier

# -------------------------
# 1. Load dataset
# -------------------------
dataset_file = "ml_dataset.pkl"

try:
    with open(dataset_file, "rb") as f:
        data = pickle.load(f)
    X = data["X"]
    y = data["y"]
    print(f"[INFO] Loaded dataset from '{dataset_file}' with {len(X)} samples")
except FileNotFoundError:
    print(f"[ERROR] Dataset file '{dataset_file}' not found! Run 'generate_dataset.py' first.")
    exit(1)

# -------------------------
# 2. Train Random Forest Classifier
# -------------------------
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)
print("[INFO] Random Forest trained successfully")

# -------------------------
# 3. Save trained model
# -------------------------
with open("trained_model.pkl", "wb") as f:
    pickle.dump(clf, f)

print("[SUCCESS] 'trained_model.pkl' has been created!")
print("[TIP] Restart your GUI to see ML-based risk predictions in action.")
