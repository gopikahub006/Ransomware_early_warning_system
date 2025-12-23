Ransomware Early Warning System

Overview
The Ransomware Early Warning System is a Python-based tool for real-time monitoring of file system activity to detect potential ransomware attacks. It combines heuristic risk scoring and machine learning predictions to alert users proactively.

Features

Real-time monitoring: create, modify, rename, delete files

Hybrid risk scoring: Heuristic (60%), ML-based (40%)

Visual risk graph with status:

SAFE – Green

HIGH RISK – Orange

RANSOMWARE ATTACK – Red

Audio alerts on risk escalation

Optional email alerts via Google App Passwords

Simulation modes: NORMAL (low-risk), MALICIOUS (high-risk)

Real folder monitoring with folder selection

Installation

Clone/download project folder

Install dependencies:

pip install -r requirements.txt


Ensure Python 3.11+ is installed

Place trained_model.pkl in project root

Usage

Run the application:

python app.py


Configure email (optional)

Start:

NORMAL Simulation → low-risk events

MALICIOUS Simulation → high-risk events

REAL Monitoring → monitor selected folder

Monitor risk score, status, logs, and graph

Alerts are sent via audio and email (if configured)

Project Structure

ransomware_early_warning_system/
├── app.py
├── trained_model.pkl
├── core_logic/
│   ├── risk_engine.py
│   ├── event_simulator.py
│   ├── real_monitor.py
│   └── ml_features.py
├── gui/main_gui.py
├── info.html
├── requirements.txt
└── README.md


Dependencies
Python 3.11+, Matplotlib, Watchdog, NumPy, Pandas, scikit-learn

License
For academic and personal use only. Do not distribute commercially.