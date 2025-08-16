import tkinter as tk
from tkinter import messagebox
import threading
import time
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd

# Import the ITC503 driver from pymeasure
try:
    from pymeasure.instruments.oxfordinstruments import ITC503
    import pyvisa  # Required for VISA errors and resource management
except ImportError:
    messagebox.showerror("Import Error",
                         "Pymeasure or PyVISA not found. Please install them using:\n"
                         "pip install pymeasure pyvisa")
    exit()

# Configure logging for the application (optional, but good for debugging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ITC503ControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Oxford Instruments ITC 503 Controller")
        master.geometry("900x750")  # Set a larger initial window size

        self.itc = None  # Instrument instance
        self.read_thread = None
        self.running_read = False
        self.data = pd.DataFrame(columns=['timestamp', 'time_elapsed_minutes', 'temperature_K'])
        self.start_time = None

        self.create_widgets()
        self.setup_plot()

        # Handle window closing
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- Connection Frame ---
        conn_frame = tk.LabelFrame(self.master, text="Instrument Connection", padx=10, pady=10)
        conn_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(conn_frame, text="VISA Address (e.g., GPIB::24, ASRL5::INSTR):").grid(row=0, column=0, sticky=tk.W,
                                                                                       pady=2)
        self.address_entry = tk.Entry(conn_frame, width=40)
        self.address_entry.grid(row=0, column=1, padx=5, pady=2)
        self.address_entry.insert(0, 'GPIB::24')  # Default address, adjust as needed

        self.connect_button = tk.Button(conn_frame, text="Connect", command=self.connect_instrument)
        self.connect_button.grid(row=0, column=2, padx=5, pady=2)

        self.disconnect_button = tk.Button(conn_frame, text="Disconnect", command=self.disconnect_instrument,
                                           state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=3, padx=5, pady=2)

        self.conn_status_label = tk.Label(conn_frame, text="Status: Disconnected", fg="red")
        self.conn_status_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)

        # --- Temperature Control Frame ---
        temp_frame = tk.LabelFrame(self.master, text="Temperature Control", padx=10, pady=10)
        temp_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(temp_frame, text="Target Temperature (K):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.temp_setpoint_entry = tk.Entry(temp_frame, width=15)
        self.temp_setpoint_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.temp_setpoint_entry.insert(0, '300.0')

        self.set_temp_button = tk.Button(temp_frame, text="Set Temperature", command=self.set_temperature,
                                         state=tk.DISABLED)
        self.set_temp_button.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(temp_frame, text="Current Temperature (K, Sensor 1):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_temp_label = tk.Label(temp_frame, text="N/A", fg="blue", font=("Arial", 12, "bold"))
        self.current_temp_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        self.start_read_button = tk.Button(temp_frame, text="Start Live Read", command=self.start_live_read,
                                           state=tk.DISABLED)
        self.start_read_button.grid(row=1, column=2, padx=5, pady=2)

        self.stop_read_button = tk.Button(temp_frame, text="Stop Live Read", command=self.stop_live_read,
                                          state=tk.DISABLED)
        self.stop_read_button.grid(row=1, column=3, padx=5, pady=2)

        # --- PID Control Frame ---
        pid_frame = tk.LabelFrame(self.master, text="PID Control Values", padx=10, pady=10)
        pid_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(pid_frame, text="Proportional (P):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.p_entry = tk.Entry(pid_frame, width=10)
        self.p_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.p_entry.insert(0, '10.0')  # Example default

        tk.Label(pid_frame, text="Integral (I):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.i_entry = tk.Entry(pid_frame, width=10)
        self.i_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.i_entry.insert(0, '5.0')  # Example default

        tk.Label(pid_frame, text="Derivative (D):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.d_entry = tk.Entry(pid_frame, width=10)
        self.d_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.d_entry.insert(0, '0.0')  # Example default

        self.set_pid_button = tk.Button(pid_frame, text="Set PID Values", command=self.set_pid_values,
                                        state=tk.DISABLED)
        self.set_pid_button.grid(row=0, column=2, rowspan=3, padx=5, pady=2, sticky=tk.NS)

        # --- Data Save Button ---
        save_frame = tk.Frame(self.master, padx=10, pady=5)
        save_frame.pack(fill=tk.X)
        self.save_button = tk.Button(save_frame, text="Save Data (CSV)", command=self.save_data, state=tk.DISABLED)
        self.save_button.pack(pady=5)

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], 'b-o', markersize=4)
        self.ax.set_xlabel("Time Elapsed (minutes)")
        self.ax.set_ylabel("Temperature (K)")
        self.ax.set_title("Live Temperature Monitoring (Sensor 1)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Add Matplotlib toolbar for zooming, panning, etc.
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()
        self.canvas_widget.pack()

    def update_connection_status(self, message, color="black"):
        self.conn_status_label.config(text=f"Status: {message}", fg=color)
        self.master.update_idletasks()

    def update_gui_state_on_connect(self, connected):
        if connected:
            self.address_entry.config(state=tk.DISABLED)
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.set_temp_button.config(state=tk.NORMAL)
            self.set_pid_button.config(state=tk.NORMAL)
            self.start_read_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)  # Can save data after connection, even if no measurements yet
        else:
            self.address_entry.config(state=tk.NORMAL)
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            self.set_temp_button.config(state=tk.DISABLED)
            self.set_pid_button.config(state=tk.DISABLED)
            self.start_read_button.config(state=tk.DISABLED)
            self.stop_read_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            self.current_temp_label.config(text="N/A")

    def connect_instrument(self):
        address = self.address_entry.get().strip()
        if not address:
            messagebox.showerror("Input Error", "Please enter a VISA address.")
            return

        self.update_connection_status("Connecting...", "orange")
        try:
            # Initialize ITC503. The default read_termination is '\n', but Oxford instruments
            # often use '\r'. We can set it during initialization or let pymeasure handle it
            # if the driver itself sets it.
            self.itc = ITC503(address)

            # Perform a test command to verify connection
            # Getting the IDN is a good way to test, as shown in the ILM test script
            idn_info = self.itc.id
            if not idn_info:  # pymeasure's .id property returns a string
                raise ConnectionError("Failed to get ID from instrument. Check address.")

            # Set control mode to Remote Unlocked (RU) to allow programmatic control
            # This is crucial for Oxford Instruments devices.
            self.itc.control_mode = "RU"
            # Set heater/gas mode to Auto (assuming you want automatic control)
            self.itc.heater_gas_mode = "AUTO"
            # Enable auto PID if desired
            self.itc.auto_pid = True  # This might be important for the PID values to take effect

            self.update_connection_status(f"Connected to {idn_info}", "green")
            self.update_gui_state_on_connect(True)
            logging.info(f"Successfully connected to ITC 503: {idn_info}")

        except pyvisa.errors.VisaIOError as e:
            self.update_connection_status(f"Connection Failed: {e}", "red")
            messagebox.showerror("Connection Error", f"Failed to connect to ITC 503:\n{e}\n"
                                                     "Please check the address, physical connection, and VISA backend.")
            self.itc = None
            self.update_gui_state_on_connect(False)
        except Exception as e:
            self.update_connection_status(f"Connection Failed: {e}", "red")
            messagebox.showerror("Connection Error", f"An unexpected error occurred during connection:\n{e}")
            self.itc = None
            self.update_gui_state_on_connect(False)

    def disconnect_instrument(self):
        if self.itc:
            self.stop_live_read()  # Stop any ongoing reading first
            try:
                # Set to Local Locked (LL) before closing for safety
                self.itc.control_mode = "LL"
                self.itc.shutdown()  # Gracefully close the instrument connection
                logging.info("ITC 503 disconnected.")
            except Exception as e:
                logging.error(f"Error during disconnect: {e}")
                messagebox.showwarning("Disconnect Error", f"Error during disconnect:\n{e}")
            finally:
                self.itc = None
                self.update_connection_status("Disconnected", "red")
                self.update_gui_state_on_connect(False)
        else:
            self.update_connection_status("Already disconnected", "red")
            self.update_gui_state_on_connect(False)

    def set_temperature(self):
        if not self.itc:
            messagebox.showerror("Error", "Not connected to ITC 503.")
            return

        try:
            temp = float(self.temp_setpoint_entry.get())
            # Validate temperature range if known for ITC 503 (e.g., 0.3 K to 1500 K)
            if not (0.3 <= temp <= 1500):
                messagebox.showwarning("Input Warning",
                                       "Temperature out of typical ITC 503 range (0.3-1500 K). Proceeding anyway.")

            self.itc.temperature_setpoint = temp
            messagebox.showinfo("Success", f"Temperature set to {temp} K.")
            logging.info(f"Temperature set to {temp} K.")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid temperature value. Please enter a number.")
        except Exception as e:
            messagebox.showerror("Instrument Error", f"Failed to set temperature: {e}")
            logging.error(f"Failed to set temperature: {e}")

    def set_pid_values(self):
        if not self.itc:
            messagebox.showerror("Error", "Not connected to ITC 503.")
            return

        try:
            p = float(self.p_entry.get())
            i = float(self.i_entry.get())
            d = float(self.d_entry.get())

            # Validate PID ranges (from pymeasure docs, e.g., P: 0.1-1000, I: 0.1-140, D: 0-273)
            if not (0.1 <= p <= 1000 and 0.1 <= i <= 140 and 0 <= d <= 273):
                messagebox.showwarning("Input Warning", "PID values are outside typical ranges. Proceeding anyway.")

            self.itc.proportional = p
            self.itc.integral = i
            self.itc.derivative = d
            messagebox.showinfo("Success", f"PID values set: P={p}, I={i}, D={d}")
            logging.info(f"PID values set: P={p}, I={i}, D={d}")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid PID values. Please enter numbers.")
        except Exception as e:
            messagebox.showerror("Instrument Error", f"Failed to set PID values: {e}")
            logging.error(f"Failed to set PID values: {e}")

    def start_live_read(self):
        if not self.itc:
            messagebox.showerror("Error", "Not connected to ITC 503.")
            return
        if self.running_read:
            messagebox.showinfo("Info", "Live reading is already running.")
            return

        self.running_read = True
        self.data = pd.DataFrame(columns=['timestamp', 'time_elapsed_minutes', 'temperature_K'])
        self.start_time = time.time()
        self.start_read_button.config(state=tk.DISABLED)
        self.stop_read_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)  # Disable save while reading live data

        self.read_thread = threading.Thread(target=self._live_read_loop)
        self.read_thread.daemon = True  # Allow thread to exit with main app
        self.read_thread.start()
        self.update_connection_status("Live reading started...", "blue")

    def stop_live_read(self):
        self.running_read = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)  # Wait for thread to finish
        self.start_read_button.config(state=tk.NORMAL)
        self.stop_read_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)  # Enable save button after stopping
        self.update_connection_status("Live reading stopped.", "black")

    def _live_read_loop(self):
        while self.running_read:
            try:
                # Read temperature from Sensor 1
                temp_k = self.itc.temperature_1.get()
                if temp_k is None:
                    raise ValueError("Could not read valid temperature from sensor.")

                current_time = time.time()
                time_elapsed_minutes = (current_time - self.start_time) / 60.0

                new_row = pd.DataFrame([{
                    'timestamp': datetime.fromtimestamp(current_time),
                    'time_elapsed_minutes': time_elapsed_minutes,
                    'temperature_K': temp_k
                }])
                self.data = pd.concat([self.data, new_row], ignore_index=True)

                self.master.after(0, self.update_current_temp_label, temp_k)  # Update label on main thread
                self.master.after(0, self.update_plot)  # Update plot on main thread

            except Exception as e:
                logging.error(f"Error during live temperature read: {e}")
                self.master.after(0, messagebox.showerror, "Read Error",
                                  f"Error reading temperature: {e}. Stopping live read.")
                self.master.after(0, self.stop_live_read)  # Stop read and update GUI state
                break  # Exit loop on error

            time.sleep(1)  # Read every 1 second (adjust as needed)

    def update_current_temp_label(self, temperature):
        self.current_temp_label.config(text=f"{temperature:.3f} K")

    def update_plot(self):
        self.ax.clear()
        if not self.data.empty:
            self.ax.plot(self.data['time_elapsed_minutes'], self.data['temperature_K'], 'b-o', markersize=4)
            self.ax.set_xlabel("Time Elapsed (minutes)")
            self.ax.set_ylabel("Temperature (K)")
            self.ax.set_title("Live Temperature Monitoring (Sensor 1)")
            self.ax.grid(True)
            # Adjust x-axis limits to show recent data or expand
            self.ax.set_xlim(left=0, right=self.data['time_elapsed_minutes'].max() * 1.1 or 1)
            # Adjust y-axis limits to be slightly wider than data range
            min_temp = self.data['temperature_K'].min()
            max_temp = self.data['temperature_K'].max()
            self.ax.set_ylim(bottom=max(0, min_temp - 5), top=max_temp + 5)
        else:
            self.ax.set_title("Live Temperature Monitoring (No Data)")
            self.ax.set_xlabel("Time Elapsed (minutes)")
            self.ax.set_ylabel("Temperature (K)")
            self.ax.set_ylim(0, 300)  # Default y-limits for initial empty plot
        self.canvas.draw_idle()

    def save_data(self):
        if self.data.empty:
            messagebox.showinfo("No Data", "No data to save.")
            return

        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Temperature Data"
        )
        if file_path:
            try:
                self.data.to_csv(file_path, index=False)
                messagebox.showinfo("Save Data", f"Data saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            self.disconnect_instrument()  # Ensure instrument is disconnected
            self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ITC503ControlApp(root)
    root.mainloop()