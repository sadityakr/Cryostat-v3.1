"""
Mercury iPS-M Test GUI

A minimal testing interface for the Oxford Instruments Mercury iPS-M magnet power supply.
This GUI allows testing of all driver functions with real-time display of values.

Author: Generated for Cryostat-v3
Date: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging

# Import the existing driver
from mercuryips import MercuryIps


class MercuryIPSTestGUI:
    """
    Minimal testing GUI for Mercury iPS-M magnet power supply
    """
    
    def __init__(self, root):
        """
        Initialize the test GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Mercury iPS-M Test GUI")
        self.root.geometry("600x700")
        
        # Initialize driver
        self.mercury_ips = None
        self.connected = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create GUI elements
        self._create_widgets()
        self._setup_layout()
        
        # Start update thread
        self.update_thread = None
        self.stop_update = False
        self._start_update_thread()
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        
        # Connection frame
        self.connection_frame = ttk.LabelFrame(self.root, text="Connection", padding="10")
        
        # Connection mode
        ttk.Label(self.connection_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.mode_var = tk.StringVar(value="ip")
        mode_combo = ttk.Combobox(self.connection_frame, textvariable=self.mode_var, 
                                 values=["ip", "visa"], state="readonly", width=10)
        mode_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # IP Address
        ttk.Label(self.connection_frame, text="IP Address:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.ip_var = tk.StringVar(value="192.168.1.100")
        self.ip_entry = ttk.Entry(self.connection_frame, textvariable=self.ip_var, width=15)
        self.ip_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Port
        ttk.Label(self.connection_frame, text="Port:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.port_var = tk.StringVar(value="7020")
        self.port_entry = ttk.Entry(self.connection_frame, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        # VISA Resource
        ttk.Label(self.connection_frame, text="VISA Resource:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.visa_var = tk.StringVar(value="GPIB0::1::INSTR")
        self.visa_entry = ttk.Entry(self.connection_frame, textvariable=self.visa_var, width=20)
        self.visa_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=2)
        
        # Connect button
        self.connect_btn = ttk.Button(self.connection_frame, text="Connect", command=self._connect)
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(self.connection_frame, text="Disconnect", command=self._disconnect, state="disabled")
        self.disconnect_btn.grid(row=3, column=2, columnspan=2, pady=10)
        
        # Connection status
        self.status_label = ttk.Label(self.connection_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=5)
        
        # Field control frame
        self.field_frame = ttk.LabelFrame(self.root, text="Field Control", padding="10")
        
        # Current field display
        ttk.Label(self.field_frame, text="Current Field:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.field_var = tk.StringVar(value="0.000 T")
        self.field_label = ttk.Label(self.field_frame, textvariable=self.field_var, font=("Arial", 12, "bold"))
        self.field_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Set field
        ttk.Label(self.field_frame, text="Set Field:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.set_field_var = tk.StringVar(value="0.0")
        self.set_field_entry = ttk.Entry(self.field_frame, textvariable=self.set_field_var, width=10)
        self.set_field_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.field_frame, text="T").grid(row=1, column=2, sticky="w", padx=2, pady=2)
        
        self.set_field_btn = ttk.Button(self.field_frame, text="Set Field", command=self._set_field)
        self.set_field_btn.grid(row=1, column=3, padx=5, pady=2)
        
        # Ramp rate
        ttk.Label(self.field_frame, text="Ramp Rate:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.ramp_rate_var = tk.StringVar(value="1.0")
        self.ramp_rate_entry = ttk.Entry(self.field_frame, textvariable=self.ramp_rate_var, width=10)
        self.ramp_rate_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.field_frame, text="T/min").grid(row=2, column=2, sticky="w", padx=2, pady=2)
        
        self.set_ramp_btn = ttk.Button(self.field_frame, text="Set Rate", command=self._set_ramp_rate)
        self.set_ramp_btn.grid(row=2, column=3, padx=5, pady=2)
        
        # Current ramp rate display
        ttk.Label(self.field_frame, text="Current Rate:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.current_rate_var = tk.StringVar(value="0.000 T/min")
        self.current_rate_label = ttk.Label(self.field_frame, textvariable=self.current_rate_var)
        self.current_rate_label.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Control buttons frame
        self.control_frame = ttk.LabelFrame(self.root, text="Control", padding="10")
        
        # Field control buttons
        self.zero_btn = ttk.Button(self.control_frame, text="Ramp to Zero", command=self._ramp_to_zero)
        self.zero_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.hold_btn = ttk.Button(self.control_frame, text="Hold Field", command=self._hold_field)
        self.hold_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.clamp_btn = ttk.Button(self.control_frame, text="Clamp", command=self._clamp)
        self.clamp_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Read buttons frame
        self.read_frame = ttk.LabelFrame(self.root, text="Read Values", padding="10")
        
        # Read buttons
        self.read_field_btn = ttk.Button(self.read_frame, text="Read Field", command=self._read_field)
        self.read_field_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.read_rate_btn = ttk.Button(self.read_frame, text="Read Rate", command=self._read_rate)
        self.read_rate_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.read_current_btn = ttk.Button(self.read_frame, text="Read Current", command=self._read_current)
        self.read_current_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Status display frame
        self.status_frame = ttk.LabelFrame(self.root, text="Status Display", padding="10")
        
        # Status displays
        ttk.Label(self.status_frame, text="Lead Current:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.lead_current_var = tk.StringVar(value="0.000 A")
        self.lead_current_label = ttk.Label(self.status_frame, textvariable=self.lead_current_var)
        self.lead_current_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(self.status_frame, text="Current Setpoint:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.current_setpoint_var = tk.StringVar(value="0.000 A")
        self.current_setpoint_label = ttk.Label(self.status_frame, textvariable=self.current_setpoint_var)
        self.current_setpoint_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(self.status_frame, text="Field Setpoint:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.field_setpoint_var = tk.StringVar(value="0.000 T")
        self.field_setpoint_label = ttk.Label(self.status_frame, textvariable=self.field_setpoint_var)
        self.field_setpoint_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=999, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
    
    def _setup_layout(self):
        """Setup the layout of all widgets"""
        
        # Main layout using grid
        self.connection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.field_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.control_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.read_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.status_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
    
    def _update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=message)
        self.logger.info(message)
    
    def _connect(self):
        """Connect to the Mercury iPS-M"""
        try:
            # Get connection parameters
            mode = self.mode_var.get()
            ip_address = self.ip_var.get()
            port = int(self.port_var.get())
            resource_name = self.visa_var.get()
            
            # Create driver instance
            if mode == "ip":
                self.mercury_ips = MercuryIps(mode=mode, ip_address=ip_address, port=port)
            else:
                self.mercury_ips = MercuryIps(mode=mode, resource_name=resource_name)
            
            # Test connection by reading field
            try:
                field = self.mercury_ips.z_magnet.magnetic_field
                self.connected = True
                self.status_label.config(text="Status: Connected", foreground="green")
                self.connect_btn.config(state="disabled")
                self.disconnect_btn.config(state="normal")
                self._update_status(f"Connected successfully. Current field: {field} T")
            except Exception as e:
                self._update_status(f"Connection test failed: {e}")
                messagebox.showerror("Connection Error", f"Failed to connect: {e}")
                
        except Exception as e:
            self._update_status(f"Connection error: {e}")
            messagebox.showerror("Connection Error", f"Connection error: {e}")
    
    def _disconnect(self):
        """Disconnect from the Mercury iPS-M"""
        try:
            self.mercury_ips = None
            self.connected = False
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self._update_status("Disconnected from Mercury iPS-M")
            
        except Exception as e:
            self._update_status(f"Disconnect error: {e}")
    
    def _set_field(self):
        """Set the magnetic field"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            value = float(self.set_field_var.get())
            self.mercury_ips.z_magnet.field_setpoint = value
            self._update_status(f"Field setpoint set to {value} T")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for field value")
        except Exception as e:
            self._update_status(f"Failed to set field: {e}")
            messagebox.showerror("Error", f"Failed to set field: {e}")
    
    def _set_ramp_rate(self):
        """Set the ramp rate"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            value = float(self.ramp_rate_var.get())
            self.mercury_ips.z_magnet.field_ramp_rate = value
            self._update_status(f"Ramp rate set to {value} T/min")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for ramp rate")
        except Exception as e:
            self._update_status(f"Failed to set ramp rate: {e}")
            messagebox.showerror("Error", f"Failed to set ramp rate: {e}")
    
    def _ramp_to_zero(self):
        """Ramp the field to zero"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to ramp the field to zero?"):
            try:
                self.mercury_ips.z_magnet.ramp_to_zero()
                self._update_status("Started ramping field to zero")
            except Exception as e:
                self._update_status(f"Failed to ramp to zero: {e}")
                messagebox.showerror("Error", f"Failed to ramp to zero: {e}")
    
    def _hold_field(self):
        """Hold the current field"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            self.mercury_ips.z_magnet.hold()
            self._update_status("Field hold activated")
        except Exception as e:
            self._update_status(f"Failed to hold field: {e}")
            messagebox.showerror("Error", f"Failed to hold field: {e}")
    
    def _clamp(self):
        """Clamp the magnet"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            self.mercury_ips.z_magnet.clamp()
            self._update_status("Magnet clamped")
        except Exception as e:
            self._update_status(f"Failed to clamp: {e}")
            messagebox.showerror("Error", f"Failed to clamp: {e}")
    
    def _read_field(self):
        """Read the magnetic field"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            field = self.mercury_ips.z_magnet.magnetic_field
            self.field_var.set(f"{field:.3f} T")
            self._update_status(f"Field read: {field} T")
        except Exception as e:
            self._update_status(f"Failed to read field: {e}")
            messagebox.showerror("Error", f"Failed to read field: {e}")
    
    def _read_rate(self):
        """Read the ramp rate"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            rate = self.mercury_ips.z_magnet.field_ramp_rate
            self.current_rate_var.set(f"{rate:.3f} T/min")
            self._update_status(f"Ramp rate read: {rate} T/min")
        except Exception as e:
            self._update_status(f"Failed to read ramp rate: {e}")
            messagebox.showerror("Error", f"Failed to read ramp rate: {e}")
    
    def _read_current(self):
        """Read the lead current"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            current = self.mercury_ips.z_magnet.current_setpoint
            self.lead_current_var.set(f"{current:.3f} A")
            self._update_status(f"Current read: {current} A")
        except Exception as e:
            self._update_status(f"Failed to read current: {e}")
            messagebox.showerror("Error", f"Failed to read current: {e}")
    
    def _update_display(self):
        """Update all display values"""
        if not self.connected or not self.mercury_ips:
            return
        
        try:
            # Update field
            field = self.mercury_ips.z_magnet.magnetic_field
            self.field_var.set(f"{field:.3f} T")
            
            # Update ramp rate
            rate = self.mercury_ips.z_magnet.field_ramp_rate
            self.current_rate_var.set(f"{rate:.3f} T/min")
            
            # Update current
            current = self.mercury_ips.z_magnet.current_setpoint
            self.lead_current_var.set(f"{current:.3f} A")
            
            # Update setpoints
            field_setpoint = self.mercury_ips.z_magnet.field_setpoint
            self.field_setpoint_var.set(f"{field_setpoint:.3f} T")
            
            current_setpoint = self.mercury_ips.z_magnet.current_setpoint
            self.current_setpoint_var.set(f"{current_setpoint:.3f} A")
                
        except Exception as e:
            # Don't show error for every update, just log it
            self.logger.debug(f"Update error: {e}")
    
    def _start_update_thread(self):
        """Start the update thread"""
        self.stop_update = False
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Update loop running in separate thread"""
        while not self.stop_update:
            if self.connected:
                self.root.after(0, self._update_display)
            time.sleep(2.0)  # Update every 2 seconds
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_update = True
        if self.connected:
            self._disconnect()
        self.root.destroy()


def main():
    """Main function to run the test GUI"""
    root = tk.Tk()
    app = MercuryIPSTestGUI(root)
    
    # Set up closing handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 