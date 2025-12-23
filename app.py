import tkinter as tk
# Import BOTH classes from your GUI file
from gui.main_gui import RansomwareMonitorApp, EmailConfigWindow

def main():
    root = tk.Tk()
    root.withdraw()  # Keeps the main dashboard hidden at start

    # 1. Show the Email Popup first
    # This will now work because of the import above
    cfg = EmailConfigWindow(root)
    cfg.top.attributes("-topmost", True)  
    root.wait_window(cfg.top) 

    # 2. Check if credentials were entered
    if cfg.sender and cfg.password and cfg.receiver:
        print(f"[SYSTEM] Credentials received for {cfg.sender}. Launching...")
        
        email_info = {
            'sender': cfg.sender,
            'password': cfg.password,
            'receiver': cfg.receiver
        }

        # 3. Launch the dashboard with the email data
        root.deiconify() 
        app = RansomwareMonitorApp(root, email_info) 
        root.mainloop()
    else:
        print("[EXIT] Email configuration was closed or incomplete.")
        root.destroy()

if __name__ == "__main__":
    main()