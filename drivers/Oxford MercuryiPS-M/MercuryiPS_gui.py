"""
Oxford Instruments Mercury iPS-M Magnet Power Supply GUI

This module provides a graphical user interface for controlling the 
Oxford Instruments Mercury iPS-M magnet power supply.

Author: Generated for Cryostat-v3
Date: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional
import logging

# Import the driver
from MercuryiPS_driver import MercuryiPSDriver, MockMercuryiPSDriver, MagnetStatus


class MercuryiPSGUI:
    """
    Graphical User Interface for Oxford Instruments Mercury iPS-M
    """
    
    def __init__(self, root: tk.Tk, use_mock: bool = False):
        """
        Initialize the GUI
        
        Args:
            root: Tkinter root window
            use_mock: Whether to use mock driver for testing
        """
        self.root = root
        self.root.title("Oxford Instruments Mercury iPS-M Control")
        self.root.geometry("800x700")
        
        # Initialize driver
        if use_mock:
            self.driver = MockMercuryiPSDriver()
        else:
            self.driver = MercuryiPSDriver()
        
        # GUI state variables
        self.connected = False
        self.update_thread = None
        self.stop_update = False
        
        # Timer variables for switch heater operations
        self.timer_active = False
        self.timer_thread = None
        self.timer_stop = False
        self.current_setpoint = 0.0  # Store current setpoint
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create GUI elements
        self._create_widgets()
        self._setup_layout()
        
        # Start update thread
        self._start_update_thread()
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        
        # Connection frame
        self.connection_frame = ttk.LabelFrame(self.root, text="Connection", padding="10")
        
        # Connection mode
        ttk.Label(self.connection_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.mode_var = tk.StringVar(value="visa")
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
        self.visa_var = tk.StringVar(value="ASRL1::INSTR")
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
        
        # Current control frame
        self.current_frame = ttk.LabelFrame(self.root, text="Current Control", padding="10")
        
        # Current display
        ttk.Label(self.current_frame, text="Current:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.current_var = tk.StringVar(value="0.000 A")
        self.current_label = ttk.Label(self.current_frame, textvariable=self.current_var, font=("Arial", 12, "bold"))
        self.current_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Set current
        ttk.Label(self.current_frame, text="Set Current:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.set_current_var = tk.StringVar(value="0.0")
        self.set_current_entry = ttk.Entry(self.current_frame, textvariable=self.set_current_var, width=10)
        self.set_current_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.current_frame, text="A").grid(row=1, column=2, sticky="w", padx=2, pady=2)
        
        self.set_current_btn = ttk.Button(self.current_frame, text="Set Current", command=self._set_current)
        self.set_current_btn.grid(row=1, column=3, padx=5, pady=2)
        
        # Current ramp rate
        ttk.Label(self.current_frame, text="Ramp Rate:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.current_ramp_rate_var = tk.StringVar(value="1.0")
        self.current_ramp_rate_entry = ttk.Entry(self.current_frame, textvariable=self.current_ramp_rate_var, width=10)
        self.current_ramp_rate_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.current_frame, text="A/min").grid(row=2, column=2, sticky="w", padx=2, pady=2)
        
        self.set_current_ramp_btn = ttk.Button(self.current_frame, text="Set Rate", command=self._set_current_ramp_rate)
        self.set_current_ramp_btn.grid(row=2, column=3, padx=5, pady=2)
        
        # Current ramp rate display
        ttk.Label(self.current_frame, text="Current Rate:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.current_rate_var = tk.StringVar(value="0.000 A/min")
        self.current_rate_label = ttk.Label(self.current_frame, textvariable=self.current_rate_var)
        self.current_rate_label.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Control buttons frame
        self.control_frame = ttk.LabelFrame(self.root, text="Control", padding="10")
        
        # Field control buttons
        self.zero_btn = ttk.Button(self.control_frame, text="Ramp to Zero", command=self._ramp_to_zero)
        self.zero_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.hold_btn = ttk.Button(self.control_frame, text="Hold Field", command=self._hold_field)
        self.hold_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Go to Setpoint button
        self.goto_setpoint_btn = ttk.Button(self.control_frame, text="Go to Setpoint", command=self._goto_setpoint)
        self.goto_setpoint_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Switch heater frame
        self.heater_frame = ttk.LabelFrame(self.root, text="Switch Heater", padding="10")
        
        # Heater status
        ttk.Label(self.heater_frame, text="Status:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.heater_status_var = tk.StringVar(value="Unknown")
        self.heater_status_label = ttk.Label(self.heater_frame, textvariable=self.heater_status_var)
        self.heater_status_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Timer display
        self.timer_var = tk.StringVar(value="")
        self.timer_label = ttk.Label(self.heater_frame, textvariable=self.timer_var, font=("Arial", 10, "bold"))
        self.timer_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        
        # Heater control buttons
        self.heater_on_btn = ttk.Button(self.heater_frame, text="Heater ON", command=self._heater_on)
        self.heater_on_btn.grid(row=2, column=0, padx=5, pady=5)
        
        self.heater_off_btn = ttk.Button(self.heater_frame, text="Heater OFF", command=self._heater_off)
        self.heater_off_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        
        # Magnet status
        ttk.Label(self.status_frame, text="Magnet Status:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.magnet_status_var = tk.StringVar(value="Unknown")
        self.magnet_status_label = ttk.Label(self.status_frame, textvariable=self.magnet_status_var)
        self.magnet_status_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Current setpoint display
        ttk.Label(self.status_frame, text="Current Setpoint:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.current_setpoint_var = tk.StringVar(value="0.000 A")
        self.current_setpoint_label = ttk.Label(self.status_frame, textvariable=self.current_setpoint_var, font=("Arial", 10, "bold"))
        self.current_setpoint_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Persistent current
        ttk.Label(self.status_frame, text="Persistent Current:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.persistent_current_var = tk.StringVar(value="0.000 A")
        self.persistent_current_label = ttk.Label(self.status_frame, textvariable=self.persistent_current_var)
        self.persistent_current_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Voltage
        ttk.Label(self.status_frame, text="Voltage:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.voltage_var = tk.StringVar(value="0.000 V")
        self.voltage_label = ttk.Label(self.status_frame, textvariable=self.voltage_var)
        self.voltage_label.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Log frame
        self.log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, padx=5, pady=5)
        
        # Clear log button
        self.clear_log_btn = ttk.Button(self.log_frame, text="Clear Log", command=self._clear_log)
        self.clear_log_btn.grid(row=1, column=0, pady=5)
        
        # Store all widgets for timer functionality
        self.all_widgets = []
        self._collect_widgets()
    
    def _collect_widgets(self):
        """Collect all widgets for timer functionality"""
        # Collect all frames and their children
        frames = [self.connection_frame, self.current_frame, self.control_frame, 
                 self.heater_frame, self.status_frame, self.log_frame]
        
        for frame in frames:
            self.all_widgets.append(frame)
            for child in frame.winfo_children():
                self.all_widgets.append(child)
                # Recursively collect children of children
                for grandchild in child.winfo_children():
                    self.all_widgets.append(grandchild)
    
    def _setup_layout(self):
        """Setup the layout of all widgets"""
        
        # Main layout using grid
        self.connection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.current_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.heater_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.log_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
    
    def _log_message(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.logger.info(message)
    
    def _clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
    
    def _fade_ui(self, fade_out: bool):
        """Fade the UI in or out"""
        if fade_out:
            # Fade out - disable all widgets and make them appear dimmed
            for widget in self.all_widgets:
                try:
                    if hasattr(widget, 'config'):
                        widget.config(state="disabled")
                        # For labels and other widgets, change foreground to gray
                        if hasattr(widget, 'cget') and widget.cget('text'):
                            widget.config(foreground="gray")
                except:
                    pass
        else:
            # Fade in - re-enable all widgets and restore normal appearance
            for widget in self.all_widgets:
                try:
                    if hasattr(widget, 'config'):
                        widget.config(state="normal")
                        # Restore normal foreground color
                        if hasattr(widget, 'cget') and widget.cget('text'):
                            widget.config(foreground="black")
                except:
                    pass
    
    def _start_timer(self):
        """Start the 60-second timer for switch heater operations"""
        if self.timer_active:
            return  # Timer already active
        
        self.timer_active = True
        self.timer_stop = False
        self._fade_ui(True)  # Fade out UI
        self._log_message("Switch heater timer started - UI disabled for 60 seconds")
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
    
    def _timer_loop(self):
        """Timer loop running in separate thread"""
        for remaining in range(60, 0, -1):
            if self.timer_stop:
                break
            
            # Update timer display
            self.root.after(0, lambda t=remaining: self.timer_var.set(f"Timer: {t}s"))
            time.sleep(1.0)
        
        # Timer finished
        self.root.after(0, self._timer_finished)
    
    def _timer_finished(self):
        """Handle timer completion"""
        self.timer_active = False
        self.timer_var.set("")
        self._fade_ui(False)  # Fade in UI
        self._log_message("Switch heater timer finished - UI re-enabled")
    
    def _connect(self):
        """Connect to the Mercury iPS-M"""
        try:
            # Get connection parameters
            mode = self.mode_var.get()
            ip_address = self.ip_var.get()
            port = int(self.port_var.get())
            resource_name = self.visa_var.get()
            
            # Create new driver instance
            if hasattr(self, 'driver'):
                self.driver.disconnect()
            
            if mode == "ip":
                self.driver = MercuryiPSDriver(mode=mode, ip_address=ip_address, port=port)
            else:
                self.driver = MercuryiPSDriver(mode=mode, resource_name=resource_name)
            
            # Attempt connection
            if self.driver.connect():
                self.connected = True
                self.status_label.config(text="Status: Connected", foreground="green")
                self.connect_btn.config(state="disabled")
                self.disconnect_btn.config(state="normal")
                self._log_message("Successfully connected to Mercury iPS-M")
                
                # Get device info
                info = self.driver.get_device_info()
                if info.get('identification'):
                    self._log_message(f"Device: {info['identification']}")
            else:
                self._log_message("Failed to connect to Mercury iPS-M")
                messagebox.showerror("Connection Error", "Failed to connect to Mercury iPS-M")
                
        except Exception as e:
            self._log_message(f"Connection error: {e}")
            messagebox.showerror("Connection Error", f"Connection error: {e}")
    
    def _disconnect(self):
        """Disconnect from the Mercury iPS-M"""
        try:
            if hasattr(self, 'driver'):
                self.driver.disconnect()
            
            self.connected = False
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self._log_message("Disconnected from Mercury iPS-M")
            
        except Exception as e:
            self._log_message(f"Disconnect error: {e}")
    
    def _set_current(self):
        """Set the current"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            value = float(self.set_current_var.get())
            if self.driver.set_current(value):
                self.current_setpoint = value  # Store the setpoint
                self._log_message(f"Current setpoint set to {value} A")
            else:
                self._log_message(f"Failed to set current to {value} A")
                messagebox.showerror("Error", f"Failed to set current to {value} A")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for current value")
    
    def _set_current_ramp_rate(self):
        """Set the current ramp rate"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        try:
            value = float(self.current_ramp_rate_var.get())
            if self.driver.set_current_ramp_rate(value):
                self._log_message(f"Current ramp rate set to {value} A/min")
            else:
                self._log_message(f"Failed to set current ramp rate to {value} A/min")
                messagebox.showerror("Error", f"Failed to set current ramp rate to {value} A/min")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for current ramp rate")
    
    def _goto_setpoint(self):
        """Go to the current setpoint"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        if self.current_setpoint == 0.0:
            messagebox.showwarning("No Setpoint", "Please set a current value first")
            return
        
        # Use the driver's ramp_to_setpoint method
        if self.driver.ramp_to_setpoint():
            self._log_message(f"Started ramping to setpoint: {self.current_setpoint} A")
        else:
            self._log_message(f"Failed to start ramping to setpoint: {self.current_setpoint} A")
            messagebox.showerror("Error", f"Failed to start ramping to setpoint: {self.current_setpoint} A")
    
    def _ramp_to_zero(self):
        """Ramp the field to zero"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        if self.driver.set_field_zero():
            self._log_message("Started ramping field to zero")
        else:
            self._log_message("Failed to start ramping to zero")
            messagebox.showerror("Error", "Failed to start ramping to zero")
    
    def _hold_field(self):
        """Hold the current field"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        if self.driver.hold_field():
            self._log_message("Field hold activated")
        else:
            self._log_message("Failed to hold field")
            messagebox.showerror("Error", "Failed to hold field")
    
    def _check_current_safety(self) -> bool:
        """
        Check if current and persistent current are within safe limits for switch heater operations
        
        Returns:
            bool: True if safe to operate switch heater, False otherwise
        """
        try:
            current = self.driver.read_current()
            persistent_current = self.driver.read_persistent_current()
            
            if current is None or persistent_current is None:
                self._log_message("Warning: Cannot read current values - switch heater operation blocked")
                messagebox.showwarning("Safety Check Failed", 
                                     "Cannot read current values. Switch heater operation blocked for safety.")
                return False
            
            # Check if current and persistent current are within 0.1 A
            current_difference = abs(current - persistent_current)
            
            if current_difference > 0.1:
                self._log_message(f"Warning: Current difference ({current_difference:.3f} A) exceeds 0.1 A limit")
                messagebox.showwarning("Safety Check Failed", 
                                     f"Current difference ({current_difference:.3f} A) exceeds 0.1 A limit.\n"
                                     f"Current: {current:.3f} A\n"
                                     f"Persistent Current: {persistent_current:.3f} A\n\n"
                                     "Switch heater operation blocked for safety.")
                return False
            
            self._log_message(f"Safety check passed - Current difference: {current_difference:.3f} A")
            return True
            
        except Exception as e:
            self._log_message(f"Error during safety check: {e}")
            messagebox.showerror("Safety Check Error", 
                               f"Error during safety check: {e}\nSwitch heater operation blocked.")
            return False
    
    def _heater_on(self):
        """Turn switch heater on"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        # Perform safety check only when button is pressed
        if not self._check_current_safety():
            return
        
        # Only send command if safety check passes
        if self.driver.switch_heater_on():
            self._log_message("Switch heater turned ON")
            self._start_timer()  # Start the 60-second timer
        else:
            self._log_message("Failed to turn switch heater ON")
            messagebox.showerror("Error", "Failed to turn switch heater ON")
    
    def _heater_off(self):
        """Turn switch heater off"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return
        
        # Perform safety check only when button is pressed
        if not self._check_current_safety():
            return
        
        # Only send command if safety check passes
        if self.driver.switch_heater_off():
            self._log_message("Switch heater turned OFF")
            self._start_timer()  # Start the 60-second timer
        else:
            self._log_message("Failed to turn switch heater OFF")
            messagebox.showerror("Error", "Failed to turn switch heater OFF")
    
    def _update_display(self):
        """Update all display values"""
        if not self.connected:
            return
        
        try:
            # Update current
            current = self.driver.read_current()
            if current is not None:
                self.current_var.set(f"{current:.3f} A")
            
            # Update current ramp rate
            rate = self.driver.read_current_ramp_rate()
            if rate is not None:
                self.current_rate_var.set(f"{rate:.3f} A/min")
            
            # Update heater status
            heater_status = self.driver.read_switch_heater_status()
            if heater_status is not None:
                self.heater_status_var.set(heater_status)
                if heater_status == "ON":
                    self.heater_status_label.config(foreground="red")
                else:
                    self.heater_status_label.config(foreground="black")
            
            # Update magnet status
            magnet_status = self.driver.read_magnet_status()
            if magnet_status != MagnetStatus.UNKNOWN:
                self.magnet_status_var.set(magnet_status.value)
                if magnet_status == MagnetStatus.RAMPING_TO_ZERO:
                    self.magnet_status_label.config(foreground="orange")
                elif magnet_status == MagnetStatus.RAMPING_TO_SET:
                    self.magnet_status_label.config(foreground="blue")
                else:
                    self.magnet_status_label.config(foreground="black")
            
            # Update current setpoint display
            current_setpoint = self.driver.read_current_setpoint()
            if current_setpoint is not None:
                self.current_setpoint_var.set(f"{current_setpoint:.3f} A")
                self.current_setpoint = current_setpoint  # Update stored setpoint
            
            # Update persistent current
            persistent_current = self.driver.read_persistent_current()
            if persistent_current is not None:
                self.persistent_current_var.set(f"{persistent_current:.3f} A")
            
            # Update voltage
            voltage = self.driver.read_voltage()
            if voltage is not None:
                self.voltage_var.set(f"{voltage:.3f} V")
                
        except Exception as e:
            self._log_message(f"Update error: {e}")
    
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
            time.sleep(1.0)  # Update every second
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_update = True
        self.timer_stop = True  # Stop timer if running
        if self.connected:
            self._disconnect()
        self.root.destroy()


def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    
    # Check if mock mode is requested
    import sys
    use_mock = "--mock" in sys.argv
    
    app = MercuryiPSGUI(root, use_mock=use_mock)
    
    # Set up closing handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 