import time
import webbrowser
import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog
import pickle
from datetime import datetime
import winsound  # For Windows beep sounds

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core_logic.risk_engine import RiskModel
from core_logic.event_simulator import EventSimulator
from core_logic.real_monitor import RealFileMonitor
from core_logic.ml_features import extract_features
import smtplib
from email.mime.text import MIMEText
from tkinter import messagebox

# -----------------------------
# Configuration
# -----------------------------
RANSOMWARE_THRESHOLD = 130
HIGH_RISK_THRESHOLD = 80
UI_UPDATE_INTERVAL_MS = 500
ML_WINDOW_SECONDS = 10  # window for feature extraction
EMAIL_COOLDOWN_SECONDS = 120

SEVERITY_COLOR = {
    "HIGH": "red",
    "MEDIUM": "#FF8C00",
    "LOW": "green"
}

# -----------------------------
# Email Alert Function
# -----------------------------
def send_alert_email(app, subject, body):
    # Safety check (VERY IMPORTANT)
    if not app.email_sender or not app.email_password or not app.email_receiver:
        print("[EMAIL] Skipped (email not configured)")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = app.email_sender
    msg["To"] = app.email_receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(app.email_sender, app.email_password)
            server.send_message(msg)
        print("[AUTO-RESPONSE] Email sent")

    except Exception as e:
        print("[EMAIL ERROR]", e)
class EmailConfigWindow:
    def __init__(self, root):
        self.top = tk.Toplevel(root)
        self.top.title("Email Configuration")
        self.top.geometry("350x220")
        self.top.resizable(False, False)
        self.top.grab_set()  # make this window modal

        tk.Label(self.top, text="Sender Email").pack(pady=5)
        self.sender_entry = tk.Entry(self.top, width=40)
        self.sender_entry.pack()

        tk.Label(self.top, text="App Password").pack(pady=5)
        self.pass_entry = tk.Entry(self.top, width=40, show="*")
        self.pass_entry.pack()

        tk.Label(self.top, text="Receiver Email").pack(pady=5)
        self.receiver_entry = tk.Entry(self.top, width=40)
        self.receiver_entry.pack()

        tk.Button(self.top, text="Continue", command=self.save).pack(pady=15)

        # Attributes to store the user input
        self.sender = None
        self.password = None
        self.receiver = None

    def save(self):
        self.sender = self.sender_entry.get().strip()
        self.password = self.pass_entry.get().strip()
        self.receiver = self.receiver_entry.get().strip()

        if not self.sender or not self.password or not self.receiver:
            tk.messagebox.showerror("Error", "All fields are required")
            return

        self.top.destroy()
class RansomwareMonitorApp:
    def __init__(self, root, email_data):
        self.root = root
        self.root.title("Ransomware Early Warning System")
        self.root.geometry("1000x800")

        # Set email credentials
        self.email_sender = email_data['sender']
        self.email_password = email_data['password']
        self.email_receiver = email_data['receiver']
        self.last_email_time = 0

        self.risk_model = RiskModel()
        self.event_queue = queue.Queue()
        self.recent_events = []

        self.ml_enabled = False
        self.ml_model = None
        try:
            with open("trained_model.pkl", "rb") as f:
                self.ml_model = pickle.load(f)
            self.ml_enabled = True
            print("[INFO] ML Model loaded successfully.")
        except Exception as e:
            print("[WARNING] ML model not loaded:", e)

        self.simulator = None
        self.real_monitor = None
        self.risk_history = []
        self.time_history = []
        self.previous_status = "SAFE"

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(UI_UPDATE_INTERVAL_MS, self.update_loop)
    
    # -----------------------------
    # Build GUI
    # -----------------------------
    def build_ui(self):
        # Top Control Panel
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=6)

        ttk.Button(
            top,
            text="Start NORMAL Simulation",
            command=lambda: self.start_sim("NORMAL")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Start MALICIOUS Simulation",
            command=lambda: self.start_sim("MALICIOUS")
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Stop Monitoring",
            command=self.stop_all
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top,
            text="Start REAL Monitoring",
            command=self.start_real_monitor
        ).pack(side=tk.LEFT, padx=5)

        # Project Info Button
        ttk.Button(
            top,
            text="Project Info ℹ️",
            command=self.open_project_info
        ).pack(side=tk.RIGHT, padx=5)

        # Labels for Score and Status
        self.score_label = ttk.Label(self.root, text="Risk Score: 0", font=("Arial", 14))
        self.score_label.pack(pady=4)

        self.status_label = tk.Label(
            self.root,
            text="SAFE",
            font=("Arial", 16),
            foreground="green"
        )
        self.status_label.pack(pady=4)

        # Log Box
        self.log_text = tk.Text(self.root, height=10, state=tk.DISABLED, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=6)

        for tag, color in SEVERITY_COLOR.items():
            self.log_text.tag_config(tag, foreground=color)

        # Graph Area
        self.fig = Figure(figsize=(7, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # -----------------------------
    # Navigation / Info
    # -----------------------------
    def open_project_info(self):
        try:
            file_path = os.path.abspath("info.html")
            webbrowser.open(f"file:///{file_path}")
        except Exception as e:
            self.log(f"Browser Error: {e}", "MEDIUM")

    # -----------------------------
    # Log helper
    # -----------------------------
    def log(self, text, severity="LOW"):
        ts = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{ts}] {text}\n", severity)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    # -----------------------------
    # Simulation
    # -----------------------------
    def start_sim(self, mode):
        if self.simulator:
            self.log("Simulation already running", "MEDIUM")
            return
        self.simulator = EventSimulator(mode=mode, event_queue=self.event_queue)
        self.simulator.start()
        self.log(f"Started {mode} simulation", "LOW")

    # -----------------------------
    # Real monitoring
    # -----------------------------
    def start_real_monitor(self):
        if self.real_monitor:
            self.log("Real monitoring already running", "MEDIUM")
            return
        watch_path = filedialog.askdirectory(title="Select Folder to Monitor")
        if not watch_path:
            return
        self.real_monitor = RealFileMonitor(path=watch_path, event_queue=self.event_queue)
        self.real_monitor.start()
        self.log(f"Started REAL monitoring on {watch_path}", "LOW")

    # -----------------------------
    # Stop all monitoring
    # -----------------------------
    def stop_all(self):
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
        if self.real_monitor:
            self.real_monitor.stop()
            self.real_monitor = None
        self.log("All monitoring stopped", "LOW")

    def on_closing(self):
        try:
            self.stop_all()
        except Exception as e:
            print("[ERROR while closing]", e)
        self.root.destroy()

    # -----------------------------
    # Sound alerts
    # -----------------------------
    def play_alert(self, status):
        """Plays different beep frequencies based on risk level."""
        try:
            if status == "SAFE":
                winsound.Beep(1000, 150)
            elif status == "HIGH RISK":
                winsound.Beep(1000, 300)
                winsound.Beep(1200, 300)
            elif status == "RANSOMWARE ATTACK":
                for freq in [1000, 1200, 1400]:
                    winsound.Beep(freq, 400)
        except:
            pass  # Ignore errors on non-Windows OS or driver issues

    # -----------------------------
    # Main update loop
    # -----------------------------
    def update_loop(self):
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                if not isinstance(event, dict):
                    continue

                self.risk_model.add_event(event["timestamp"], event["risk"])
                self.recent_events.append(event)

                if len(self.recent_events) > 50:
                    self.recent_events.pop(0)

                self.log(
                    f"{event['type']}: {event['file']} (+{event['risk']})",
                    severity="HIGH" if event["risk"] >= 25 else "LOW"
                )
            except queue.Empty:
                break

        # 2. Compute Hybrid Risk Score
        heuristic_risk = self.risk_model.normalized_risk()

        ml_prob = 0
        if self.ml_enabled and self.recent_events:
            try:
                features = extract_features(
                    self.recent_events,
                    window_seconds=ML_WINDOW_SECONDS
                )
                if features:
                    ml_prob = self.ml_model.predict_proba(
                        [features[-1]]
                    )[0][1]
            except Exception:
                ml_prob = 0

        final_score_scaled = (0.6 * heuristic_risk + 0.4 * ml_prob) * 300

        self.risk_history.append(final_score_scaled)
        self.time_history.append(time.time())

        if len(self.risk_history) > 300:
            self.risk_history.pop(0)
            self.time_history.pop(0)

        # 3. Determine Status
        if final_score_scaled < HIGH_RISK_THRESHOLD:
            status = "SAFE"
            self.status_label.config(text=status, foreground="green")
        elif final_score_scaled < RANSOMWARE_THRESHOLD:
            status = "HIGH RISK"
            self.status_label.config(text=status, foreground="orange")
        else:
            status = "RANSOMWARE ATTACK"
            self.status_label.config(text=status, foreground="red")

        self.score_label.config(
            text=f"Risk Score: {int(final_score_scaled)}"
        )

        # 4. Email + Sound Alert (ONCE per attack)
        now = time.time()

        if status == "RANSOMWARE ATTACK" and status != self.previous_status:
            if now - self.last_email_time > EMAIL_COOLDOWN_SECONDS:
                send_alert_email(
                    self,
                    "🚨 RANSOMWARE DETECTED",
                    f"Risk Score: {int(final_score_scaled)}"
                )
                self.last_email_time = now

            threading.Thread(
                target=self.play_alert,
                args=(status,),
                daemon=True
            ).start()

        self.previous_status = status

        # 5. Update Graphical Visualization
        if self.time_history:
            self.ax.clear()
            self.ax.set_title("Real-Time Ransomware Risk Analysis")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Risk Intensity")

            y_max = max(200, max(self.risk_history) * 1.2)
            self.ax.set_ylim(0, y_max)

            start_time = self.time_history[0]
            times_relative = [t - start_time for t in self.time_history]

            current_color = (
                "green" if status == "SAFE"
                else "orange" if status == "HIGH RISK"
                else "red"
            )
            self.ax.plot(times_relative, self.risk_history, color=current_color, linewidth=2)

            self.ax.axhspan(0, HIGH_RISK_THRESHOLD, facecolor="green", alpha=0.05)
            self.ax.axhspan(HIGH_RISK_THRESHOLD, RANSOMWARE_THRESHOLD, facecolor="orange", alpha=0.05)
            self.ax.axhspan(RANSOMWARE_THRESHOLD, y_max, facecolor="red", alpha=0.05)

            self.canvas.draw()

        # Schedule next refresh
        self.root.after(UI_UPDATE_INTERVAL_MS, self.update_loop)

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    cfg = EmailConfigWindow(root)
    cfg.top.attributes("-topmost", True)
    root.wait_window(cfg.top)
    if cfg.sender and cfg.password and cfg.receiver:
        email_info = {'sender': cfg.sender, 'password': cfg.password, 'receiver': cfg.receiver}
        root.deiconify()
        app = RansomwareMonitorApp(root, email_info)
        root.mainloop()
    else:
        root.destroy()