import tkinter as tk
from tkinter import ttk, messagebox
from pymeasure.adapters import VISAAdapter
from oi_ilm210 import OI_ILM210
import time

class ILM210GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OI ILM 210 Control Panel")
        self.root.geometry("600x400")
        
        # Instrument variables
        self.ilm210 = None
        self.connected = False
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Resource:").grid(row=0, column=0, sticky="w")
        self.resource_var = tk.StringVar(value="ASRL4::INSTR")
        ttk.Entry(conn_frame, textvariable=self.resource_var, width=20).grid(row=0, column=1, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_instrument)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_instrument, state="disabled")
        self.disconnect_btn.grid(row=0, column=3, padx=5)
        
        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        # Connection status
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        self.status_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Read-Only Properties Frame
        read_frame = ttk.LabelFrame(self.root, text="Read-Only Properties", padding="10")
        read_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Level
        ttk.Label(read_frame, text="Level (%):").grid(row=0, column=0, sticky="w")
        self.level_var = tk.StringVar(value="--")
        ttk.Label(read_frame, textvariable=self.level_var, font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5)
        ttk.Button(read_frame, text="Read", command=self.read_level, width=8).grid(row=0, column=2, padx=5)
        
        # Status
        ttk.Label(read_frame, text="Device Status:").grid(row=1, column=0, sticky="w")
        self.device_status_var = tk.StringVar(value="--")
        ttk.Label(read_frame, textvariable=self.device_status_var).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Button(read_frame, text="Read", command=self.read_status, width=8).grid(row=1, column=2, padx=5)
        
        # Read/Write Properties Frame
        rw_frame = ttk.LabelFrame(self.root, text="Read/Write Properties", padding="10")
        rw_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # Rate
        ttk.Label(rw_frame, text="Probe Rate:").grid(row=0, column=0, sticky="w")
        self.rate_var = tk.StringVar(value="--")
        rate_combo = ttk.Combobox(rw_frame, textvariable=self.rate_var, values=["SLOW", "FAST"], state="readonly", width=10)
        rate_combo.grid(row=0, column=1, padx=5)
        ttk.Button(rw_frame, text="Read", command=self.read_rate, width=8).grid(row=0, column=2, padx=5)
        ttk.Button(rw_frame, text="Write", command=self.write_rate, width=8).grid(row=0, column=3, padx=5)
        
        # Remote Control
        ttk.Label(rw_frame, text="Remote Control:").grid(row=1, column=0, sticky="w")
        self.remote_var = tk.BooleanVar(value=False)
        remote_check = ttk.Checkbutton(rw_frame, text="Enabled", variable=self.remote_var)
        remote_check.grid(row=1, column=1, sticky="w", padx=5)
        ttk.Button(rw_frame, text="Read", command=self.read_remote_control, width=8).grid(row=1, column=2, padx=5)
        ttk.Button(rw_frame, text="Write", command=self.write_remote_control, width=8).grid(row=1, column=3, padx=5)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="ew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
    def log(self, message):
        """Add message to log with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def connect_instrument(self):
        """Connect to the instrument."""
        try:
            resource = self.resource_var.get()
            self.log(f"Connecting to {resource}...")
            
            adapter = VISAAdapter(resource)
            self.ilm210 = OI_ILM_210(adapter)
            
            # Test connection
            idn = self.ilm210.get_idn()
            self.log(f"Connected! ID: {idn}")
            
            self.connected = True
            self.status_label.config(text="Connected", foreground="green")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            
            # Initial read
            self.refresh_all()
            
        except Exception as e:
            self.log(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
    
    def disconnect_instrument(self):
        """Disconnect from the instrument."""
        try:
            if self.ilm210:
                self.ilm210.shutdown()
                self.ilm210 = None
            
            self.connected = False
            self.status_label.config(text="Disconnected", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            
            # Clear values
            self.level_var.set("--")
            self.device_status_var.set("--")
            self.rate_var.set("--")
            self.remote_var.set(False)
            
            self.log("Disconnected")
            
        except Exception as e:
            self.log(f"Disconnect error: {e}")
    
    # Simple property methods - just call driver and update UI
    def read_level(self):
        if not self.connected: return
        try:
            level = self.ilm210.level
            self.level_var.set(f"{level:.2f}" if level is not None else "Error")
            self.log(f"Read level: {level:.2f}%" if level is not None else "Error reading level")
        except Exception as e:
            self.log(f"Read level error: {e}")
    
    def read_status(self):
        if not self.connected: return
        try:
            status = self.ilm210.status
            self.device_status_var.set(status)
            self.log(f"Read status: {status}")
        except Exception as e:
            self.log(f"Read status error: {e}")
    
    def read_rate(self):
        if not self.connected: return
        try:
            rate = self.ilm210.rate
            self.rate_var.set(rate)
            self.log(f"Read rate: {rate}")
        except Exception as e:
            self.log(f"Read rate error: {e}")
    
    def read_remote_control(self):
        if not self.connected: return
        try:
            remote = self.ilm210.remote_control
            self.remote_var.set(remote)
            self.log(f"Read remote control: {remote}")
        except Exception as e:
            self.log(f"Read remote control error: {e}")
    
    def write_rate(self):
        if not self.connected: return
        try:
            rate = self.rate_var.get()
            if rate in ["SLOW", "FAST"]:
                self.ilm210.rate = rate
                self.log(f"Wrote rate: {rate}")
                self.read_rate()  # Confirm
            else:
                self.log(f"Invalid rate: {rate}")
        except Exception as e:
            self.log(f"Write rate error: {e}")
    
    def write_remote_control(self):
        if not self.connected: return
        try:
            enabled = self.remote_var.get()
            self.ilm210.remote_control = enabled
            self.log(f"Wrote remote control: {enabled}")
            self.read_remote_control()  # Confirm
        except Exception as e:
            self.log(f"Write remote control error: {e}")
    
    def refresh_all(self):
        if not self.connected: return
        try:
            self.read_level()
            self.read_status()
            self.read_rate()
            self.read_remote_control()
            self.log("Refreshed all values")
        except Exception as e:
            self.log(f"Refresh error: {e}")

def main():
    root = tk.Tk()
    app = ILM210GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
