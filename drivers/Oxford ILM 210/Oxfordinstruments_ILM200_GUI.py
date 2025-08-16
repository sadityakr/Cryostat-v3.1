import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import threading
import time
from datetime import datetime
import logging

# Import the OxfordInstruments_ILM200 class from the separate file
try:
    from OxfordInstruments_ILM200 import OxfordInstruments_ILM200
except ImportError as e:
    # Provide a helpful error message if the driver file isn't found
    messagebox.showerror("Import Error",
                         f"Could not import OxfordInstruments_ILM200.py. "
                         f"Please ensure '{e.name}.py' is in the same directory as this script.")
    exit() # Exit the application if the driver cannot be imported

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HeliumLevelMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Helium Level Monitor (Oxford ILM 210)")
        master.geometry("800x700") # Set initial window size

        self.ilm = None
        self.measurement_thread = None
        self.running = False
        self.data = pd.DataFrame(columns=['timestamp', 'time_elapsed_minutes', 'helium_level', 'status'])
        self.start_time = None

        # --- GUI Elements ---
        self.create_widgets()

        # --- Matplotlib Plot ---
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.line, = self.ax.plot([], [], 'b-o')
        self.ax.set_xlabel("Time Elapsed (minutes)")
        self.ax.set_ylabel("Helium Level (%)")
        self.ax.set_title("Live Helium Level Monitoring")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Handle window closing
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Input Frame
        input_frame = tk.Frame(self.master, padx=10, pady=10)
        input_frame.pack(fill=tk.X)

        tk.Label(input_frame, text="Instrument Address (e.g., ASRL1::INSTR):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.address_entry = tk.Entry(input_frame, width=40)
        self.address_entry.grid(row=0, column=1, padx=5, pady=2)
        self.address_entry.insert(0, 'ASRL8::INSTR') # Default value
        self.connect_button = tk.Button(input_frame, text="Connect", command=self.connect_instrument)
        self.connect_button.grid(row=0, column=2, padx=5, pady=2)
        self.close_button = tk.Button(input_frame, text="Close", command=self.close_app)
        self.close_button.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(input_frame, text="Measurement Period (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.period_entry = tk.Entry(input_frame, width=10)
        self.period_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.period_entry.insert(0, '5') # Default value
        self.period_entry.bind('<FocusOut>', self.on_period_change)
        self.period_entry.bind('<Return>', self.on_period_change)


        # --- Measurement Rate Indicator and Controls ---
        tk.Label(input_frame, text="Measurement Rate:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.rate_var = tk.StringVar(value="N/A")
        self.rate_label = tk.Label(input_frame, textvariable=self.rate_var, width=25, relief=tk.SUNKEN, anchor=tk.W)
        self.rate_label.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.refresh_rate_button = tk.Button(input_frame, text="Refresh", command=self.refresh_rate)
        self.refresh_rate_button.grid(row=2, column=2, padx=5, pady=2)
        self.slow_button = tk.Button(input_frame, text="Set to Slow", command=self.set_to_slow)
        self.slow_button.grid(row=2, column=3, padx=5, pady=2)
        self.fast_button = tk.Button(input_frame, text="Set to Fast", command=self.set_to_fast)
        self.fast_button.grid(row=2, column=4, padx=5, pady=2)

        # Control Buttons Frame
        button_frame = tk.Frame(self.master, padx=10, pady=5)
        button_frame.pack(fill=tk.X)

        self.start_button = tk.Button(button_frame, text="Start Measuring", command=self.start_measurement, state=tk.DISABLED)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(button_frame, text="Stop Measurement", command=self.stop_measurement, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.save_button = tk.Button(button_frame, text="Save Data (CSV)", command=self.save_data, state=tk.DISABLED)
        self.save_button.grid(row=0, column=2, padx=5, pady=5)

        # Status Label
        self.status_label = tk.Label(self.master, text="Status: Ready", fg="blue")
        self.status_label.pack(pady=5)

    def update_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", fg=color)
        self.master.update_idletasks() # Update GUI immediately

    def connect_instrument(self):
        address = self.address_entry.get().strip()
        if not address:
            messagebox.showerror("Input Error", "Instrument Address cannot be empty.")
            return
        # Close previous instrument if it exists
        if self.ilm is not None:
            try:
                self.ilm.close()
            except Exception:
                pass
            self.ilm = None
        try:
            self.ilm = OxfordInstruments_ILM200(name='ilm_sensor', address=address, number=1)
            idn_info = self.ilm.get_idn()
            if not idn_info or not idn_info.get('model'):
                raise ConnectionError("Failed to get IDN from instrument. Check address and connection.")
            self.update_status(f"Connected to {idn_info.get('model', 'ILM 210')}. Ready to measure.", "green")
            self.enable_controls()
            self.refresh_rate()
        except Exception as e:
            self.update_status(f"Connection failed: {e}", "red")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.disable_controls()
            self.ilm = None

    def enable_controls(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        self.period_entry.config(state=tk.NORMAL)
        self.refresh_rate_button.config(state=tk.NORMAL)
        self.slow_button.config(state=tk.NORMAL)
        self.fast_button.config(state=tk.NORMAL)

    def disable_controls(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.period_entry.config(state=tk.DISABLED)
        self.refresh_rate_button.config(state=tk.DISABLED)
        self.slow_button.config(state=tk.DISABLED)
        self.fast_button.config(state=tk.DISABLED)

    def start_measurement(self):
        period_str = self.period_entry.get().strip()
        try:
            period = int(period_str)
            if period <= 0:
                raise ValueError("Period must be a positive integer.")
        except ValueError:
            messagebox.showerror("Input Error", "Measurement Period must be a valid positive integer.")
            return
        self.period_entry.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.update_status("Starting measurement...", "orange")
        self.measurement_thread = threading.Thread(target=self._measurement_loop, args=(period,))
        self.measurement_thread.daemon = True
        self.measurement_thread.start()

    def refresh_rate(self):
        if self.ilm and hasattr(self.ilm, 'visa_handle'):
            try:
                # Try to use a public method, fallback to private if needed
                if hasattr(self.ilm, 'do_get_rate'):
                    rate = self.ilm.do_get_rate()
                elif hasattr(self.ilm, '_do_get_rate'):
                    rate = self.ilm._do_get_rate()
                else:
                    rate = "Unknown"
                self.rate_var.set(rate)
            except Exception as e:
                self.rate_var.set(f"Error: {e}")
        else:
            self.rate_var.set("Not connected")

    def set_to_slow(self):
        if self.ilm and hasattr(self.ilm, 'visa_handle'):
            try:
                self.ilm.set_to_slow()
                self.refresh_rate()
            except Exception as e:
                messagebox.showerror("Set to Slow Error", f"Failed to set to slow: {e}")
        else:
            messagebox.showwarning("Not Connected", "Instrument not connected.")

    def set_to_fast(self):
        if self.ilm and hasattr(self.ilm, 'visa_handle'):
            try:
                self.ilm.set_to_fast()
                self.refresh_rate()
            except Exception as e:
                messagebox.showerror("Set to Fast Error", f"Failed to set to fast: {e}")
        else:
            messagebox.showwarning("Not Connected", "Instrument not connected.")

    def _measurement_loop(self, period):
        import queue
        self.running = True
        self.data = pd.DataFrame(columns=['timestamp', 'time_elapsed_minutes', 'helium_level', 'status'])
        self.start_time = time.time()
        self.param_queue = queue.Queue()
        try:
            while self.running:
                # Check for parameter changes
                try:
                    param_change = self.param_queue.get_nowait()
                    if param_change == 'pause':
                        self.update_status("Measurement paused for parameter change.", "orange")
                        while True:
                            param_resume = self.param_queue.get()
                            if param_resume == 'resume':
                                self.update_status("Resuming measurement...", "green")
                                break
                except Exception:
                    pass
                # Check connection and visa_handle before sending commands
                if not self.ilm or not hasattr(self.ilm, 'visa_handle'):
                    self.update_status("Instrument not connected.", "red")
                    break
                current_time = time.time()
                time_elapsed_minutes = (current_time - self.start_time) / 60.0
                try:
                    helium_level = self.ilm.level.get() if hasattr(self.ilm, 'level') else None
                    device_status = self.ilm.status.get() if hasattr(self.ilm, 'status') else None
                    if helium_level is None:
                        raise ValueError("Could not read valid helium level.")
                    new_row = pd.DataFrame([{
                        'timestamp': datetime.fromtimestamp(current_time),
                        'time_elapsed_minutes': time_elapsed_minutes,
                        'helium_level': helium_level,
                        'status': device_status
                    }])
                    self.data = pd.concat([self.data, new_row], ignore_index=True)
                    self.master.after(0, self.update_plot)
                    self.update_status(f"Level: {helium_level:.2f}% | Status: {device_status}", "blue")
                except Exception as e:
                    self.update_status(f"Error reading data: {e}. Stopping measurement.", "red")
                    logging.error(f"Error during measurement loop: {e}")
                    self.running = False
                    break
                time.sleep(period)
        except Exception as e:
            self.update_status(f"Measurement error: {e}", "red")
            logging.error(f"Measurement error: {e}")
        finally:
            self.stop_measurement()

    def stop_measurement(self):
        self.running = False
        if hasattr(self, 'param_queue'):
            try:
                self.param_queue.put('resume')
            except Exception:
                pass
        # Wait for the measurement thread to finish
        if hasattr(self, 'measurement_thread') and self.measurement_thread is not None:
            if self.measurement_thread.is_alive():
                self.measurement_thread.join(timeout=2)
            self.measurement_thread = None
        if self.ilm:
            try:
                self.ilm.close()
                logging.info("Instrument connection closed.")
            except Exception as e:
                logging.error(f"Error closing instrument connection: {e}")
        self.ilm = None
        self.rate_var.set("N/A")
        self.address_entry.config(state=tk.NORMAL)
        self.period_entry.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
        self.update_status("Measurement stopped.", "black")

    def update_plot(self):
        self.ax.clear()
        if not self.data.empty:
            self.ax.plot(self.data['time_elapsed_minutes'], self.data['helium_level'], 'b-o', markersize=4)
            self.ax.set_xlabel("Time Elapsed (minutes)")
            self.ax.set_ylabel("Helium Level (%)")
            self.ax.set_title("Live Helium Level Monitoring")
            self.ax.grid(True)
            # Adjust x-axis limits to show recent data or expand
            self.ax.set_xlim(left=0, right=self.data['time_elapsed_minutes'].max() * 1.1 or 1)
            # Adjust y-axis limits to be slightly wider than data range, or default 0-100
            min_level = self.data['helium_level'].min()
            max_level = self.data['helium_level'].max()
            self.ax.set_ylim(bottom=max(0, min_level - 5), top=min(100, max_level + 5))
        else:
            self.ax.set_title("Live Helium Level Monitoring (No Data)")
            self.ax.set_xlabel("Time Elapsed (minutes)")
            self.ax.set_ylabel("Helium Level (%)")
            self.ax.set_ylim(0, 100) # Default y-limits
        self.canvas.draw_idle()

    def save_data(self):
        if self.data.empty:
            messagebox.showinfo("No Data", "No data to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Measurement Data"
        )
        if file_path:
            try:
                self.data.to_csv(file_path, index=False)
                messagebox.showinfo("Save Data", f"Data saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def on_period_change(self, *args):
        if self.running and hasattr(self, 'param_queue'):
            self.param_queue.put('pause')
            # Simulate confirmation and resume
            self.param_queue.put('resume')

    def close_app(self):
        self.stop_measurement()
        self.master.destroy()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            self.close_app()

# --- Main Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = HeliumLevelMonitorApp(root)
    root.mainloop()