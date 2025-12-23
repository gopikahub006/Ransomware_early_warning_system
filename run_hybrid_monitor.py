import time
import pickle
from core_logic.real_monitor import RealFileMonitor
from core_logic.risk_engine import RiskEngine

# -------------------------
# Define update_loop (Hybrid Monitoring)
# -------------------------
def update_loop(monitor, model, heuristic_engine, update_interval=1):
    """
    Real-time hybrid monitoring loop combining heuristic and ML.
    """
    while True:
        # 1️⃣ Extract ML feature vector from last 10 seconds
        feature_vector = monitor.get_feature_vector(window_seconds=10)

        # 2️⃣ Compute ML probability (label=1 for malicious)
        ml_prob = model.predict_proba([feature_vector])[0][1]

        # 3️⃣ Compute heuristic risk (normalized to 0-1)
        heuristic_risk = heuristic_engine.compute_risk()

        # 4️⃣ Hybrid final risk
        final_risk = 0.6 * heuristic_risk + 0.4 * ml_prob

        # 5️⃣ Determine status
        if final_risk > 0.8:
            status = "RANSOMWARE ATTACK"
        elif final_risk > 0.5:
            status = "HIGH RISK"
        else:
            status = "SAFE"

        # 6️⃣ Explainability reasons
        reasons = []
        modify_count, rename_count, delete_ratio, entropy, burstiness = feature_vector

        if rename_count > 5:
            reasons.append("Rapid file renaming detected")
        if delete_ratio > 0.3:
            reasons.append("High file deletion ratio")
        if burstiness > 10:
            reasons.append("Sudden burst of file operations")
        if entropy > 1.5:
            reasons.append("Highly random file behavior")

        # 7️⃣ Print status
        print(f"[STATUS] {status} | Hybrid Risk: {final_risk:.2f}")
        if reasons:
            print("Reasons:")
            for r in reasons:
                print(f" • {r}")
        print("-" * 50)

        # 8️⃣ Wait before next update
        time.sleep(update_interval)


# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    # Load trained ML model
    with open("trained_model.pkl", "rb") as f:
        model = pickle.load(f)

    # Initialize real-time monitor
    monitor = RealFileMonitor("./test_folder")  # change path as needed
    monitor.start()
    print("[INFO] Real-time monitoring started.")

    # Initialize heuristic engine
    heuristic_engine = RiskEngine(monitor.event_queue)

    # Start hybrid monitoring loop
    update_loop(monitor, model, heuristic_engine, update_interval=1)
