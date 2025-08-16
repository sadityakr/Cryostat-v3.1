import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
                             QDoubleSpinBox, QMessageBox, QGroupBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
import matplotlib

matplotlib.use('Qt5Agg')  # Use the PyQt5 backend for Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import time
import pyvisa
from Keithley6221_Delta import Keithley6221  # Import the unified Keithley6221_Delta.py


class DeltaModeTab(QWidget):
    """
    Tab for configuring and starting the Keithley 6221 Delta Mode.
    """

    def __init__(self, parent=None, get_instrument_callback=None):
        super().__init__(parent)
        self.get_instrument = get_instrument_callback  # Callback to get the instrument instance from main GUI
        self.instrument = None  # Local reference to the instrument
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface for the Delta Mode Setup tab."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Instrument Address Group
        address_group = QGroupBox("Instrument Connection")
        address_layout = QHBoxLayout()
        address_label = QLabel('VISA Address:')
        address_label.setFixedWidth(100)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., GPIB0::10::INSTR")
        self.address_input.setText("GPIB0::19::INSTR")  # Default address
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_input)

        self.connect_btn = QPushButton('Test Connection')
        self.connect_btn.clicked.connect(self.test_connection)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF; /* Blue */
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        address_layout.addWidget(self.connect_btn)
        address_group.setLayout(address_layout)
        layout.addWidget(address_group)

        # Delta Mode Parameters Group
        params_group = QGroupBox("Delta Mode Parameters")
        params_layout = QVBoxLayout()

        # Low Current
        low_current_layout = QHBoxLayout()
        low_current_layout.addWidget(QLabel('Low Level Current (A):'))
        self.low_current_input = QDoubleSpinBox()
        self.low_current_input.setDecimals(9)
        self.low_current_input.setRange(-0.105, 0.105) # Adjusted range based on pymeasure driver
        self.low_current_input.setSingleStep(1e-6)
        self.low_current_input.setValue(-1e-3)  # Default
        low_current_layout.addWidget(self.low_current_input)
        params_layout.addLayout(low_current_layout)

        # High Current
        high_current_layout = QHBoxLayout()
        high_current_layout.addWidget(QLabel('High Level Current (A):'))
        self.high_current_input = QDoubleSpinBox()
        self.high_current_input.setDecimals(9)
        self.high_current_input.setRange(0.0, 0.105) # Adjusted range based on pymeasure driver
        self.high_current_input.setSingleStep(1e-6)
        self.high_current_input.setValue(1e-3)  # Default
        high_current_layout.addWidget(self.high_current_input)
        params_layout.addLayout(high_current_layout)

        # Compliance Voltage
        compliance_layout = QHBoxLayout()
        compliance_layout.addWidget(QLabel('Compliance Voltage (V):'))
        self.compliance_input = QDoubleSpinBox()
        self.compliance_input.setDecimals(3)
        self.compliance_input.setRange(0.1, 105.0) # Adjusted range based on pymeasure driver
        self.compliance_input.setSingleStep(0.1)
        self.compliance_input.setValue(1.0)  # Default
        compliance_layout.addWidget(self.compliance_input)
        params_layout.addLayout(compliance_layout)

        # 2182A Range
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel('2182A Range (V):'))
        self.range_input = QDoubleSpinBox()
        self.range_input.setDecimals(6)
        self.range_input.setRange(0.000001, 10.0)  # From microvolt to 10V - Kept as original
        self.range_input.setSingleStep(0.001)
        self.range_input.setValue(0.01)  # Default
        range_layout.addWidget(self.range_input)
        params_layout.addLayout(range_layout)

        # Delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel('Delay (ms):'))
        self.delay_input = QSpinBox()
        self.delay_input.setRange(0, 10000) # Max 999999999 as per pymeasure driver (seconds), so 10000 ms is fine.
        self.delay_input.setValue(100)  # Default
        delay_layout.addWidget(self.delay_input)
        params_layout.addLayout(delay_layout)

        # Measurement Unit
        voltage_mode_layout = QHBoxLayout()
        voltage_mode_layout.addWidget(QLabel('Measurement Unit:'))
        self.voltage_mode_input = QComboBox()
        self.voltage_mode_input.addItems(['V', 'Ohm']) # Corresponds to 'V' and 'Ohms' in pymeasure driver
        voltage_mode_layout.addWidget(self.voltage_mode_input)
        params_layout.addLayout(voltage_mode_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Start/Stop Buttons
        control_buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton('Start Delta Mode')
        self.start_btn.clicked.connect(self.start_delta_mode)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745; /* Green */
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        control_buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Stop Delta Mode')
        self.stop_btn.clicked.connect(self.stop_delta_mode)
        self.stop_btn.setEnabled(False)  # Disabled until mode is started
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545; /* Red */
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        control_buttons_layout.addWidget(self.stop_btn)
        layout.addLayout(control_buttons_layout)

        # Status
        self.status_label = QLabel('Status: Not connected.')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def test_connection(self):
        """Tests the connection to the Keithley 6221 instrument."""
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Input Error", "Please enter a VISA address.")
            return

        self.status_label.setText('Status: Attempting to connect...')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;")
        self.connect_btn.setEnabled(False)

        # Close any existing connection before trying a new one
        if self.instrument:
            try:
                self.instrument.shutdown()
            except Exception as e:
                print(f"Error during previous instrument shutdown: {e}")
            self.instrument = None

        try:
            rm = pyvisa.ResourceManager()
            resource = rm.open_resource(address)
            resource.timeout = 5000  # 5 seconds timeout

            # Create the instrument instance with our unified Keithley6221 driver
            self.instrument = Keithley6221(resource)

            idn = self.instrument.check_connection()
            if "Connection failed" in idn:
                raise Exception(idn)

            self.status_label.setText(f'Status: Connected!\nInstrument IDN: {idn}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #28A745;")

            # Pass the instrument instance to the main GUI via callback
            if self.get_instrument:
                self.get_instrument(self.instrument)

        except Exception as e:
            self.status_label.setText(f'Status: Connection Error!\nError details: {e}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;")
            self.instrument = None  # Clear instrument on error
        finally:
            self.connect_btn.setEnabled(True)

    def start_delta_mode(self):
        """Starts the Delta Mode sequence on the Keithley 6221."""
        if not self.instrument:
            QMessageBox.warning(self, "Connection Error", "Please test connection first and ensure it's successful.")
            return

        # Validate parameters
        low_current = self.low_current_input.value()
        high_current = self.high_current_input.value()

        if not (-0.105 <= low_current <= 0.105) or not (0.0 <= high_current <= 0.105):
             QMessageBox.warning(self, "Parameter Error", "Low current must be within ±0.105 A and High current must be between 0 and 0.105 A.")
             return

        if low_current == high_current:
            QMessageBox.warning(self, "Parameter Error", "Low and high currents must be different.")
            return

        try:
            compliance_voltage = self.compliance_input.value()
            range_2182A = self.range_input.value()
            delay_ms = self.delay_input.value()
            voltage_mode_str = self.voltage_mode_input.currentText()

            self.status_label.setText('Status: Starting Delta Mode...')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;")
            self.start_btn.setEnabled(False)

            self.instrument.start_delta_mode(
                low_current, high_current, compliance_voltage,
                range_2182A, delay_ms, voltage_mode_str
            )

            self.status_label.setText('Status: Delta Mode Started.')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #007BFF;")  # Blue for active
            self.stop_btn.setEnabled(True)
            QMessageBox.information(self, "Delta Mode",
                                    "Delta Mode initiated successfully. Switch to Data Acquisition tab to read data.")

        except Exception as e:
            self.status_label.setText(f'Status: Error starting Delta Mode: {e}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;")
            QMessageBox.critical(self, "Error", f"Failed to start Delta Mode: {e}")
            self.start_btn.setEnabled(True)

    def stop_delta_mode(self):
        """Stops the Delta Mode sequence on the Keithley 6221."""
        if self.instrument:
            try:
                self.status_label.setText('Status: Stopping Delta Mode...')
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;")

                self.instrument.stop_delta_mode()

                self.status_label.setText('Status: Delta Mode Stopped.')
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)

            except Exception as e:
                self.status_label.setText(f'Status: Error stopping Delta Mode: {e}')
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;")
                QMessageBox.critical(self, "Error", f"Failed to stop Delta Mode: {e}")
        else:
            self.status_label.setText('Status: No instrument connected to stop.')
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)


class DataAcquisitionTab(QWidget):
    """
    Tab for acquiring and plotting data from the Keithley 6221 in Delta Mode.
    """

    def __init__(self, parent=None, get_instrument_callback=None):
        super().__init__(parent)
        self.get_instrument = get_instrument_callback  # Callback to get the instrument instance
        self.instrument = None  # Local reference to the instrument
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.data = pd.DataFrame(columns=['Time (s)', 'Voltage (V)', 'Resistance (Ohm)'])
        self.current_sample = 0
        self.num_samples_to_acquire = 0
        self.measurement_period = 0.0
        self.start_time = 0.0
        self.is_acquiring = False
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface for the Data Acquisition tab."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Acquisition Parameters Group
        params_group = QGroupBox("Acquisition Parameters")
        params_layout = QVBoxLayout()

        # Number of samples
        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel('Number of Samples:'))
        self.samples_input = QSpinBox()
        self.samples_input.setRange(1, 1000000) # Increased max samples to match pymeasure buffer capability
        self.samples_input.setValue(100)  # Default
        samples_layout.addWidget(self.samples_input)
        params_layout.addLayout(samples_layout)

        # Measurement period
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel('Measurement Period (s):'))
        self.period_input = QDoubleSpinBox()
        self.period_input.setDecimals(3)
        self.period_input.setRange(0.01, 60.0)  # 10 ms to 60 seconds
        self.period_input.setSingleStep(0.01)
        self.period_input.setValue(0.1)  # Default
        period_layout.addWidget(self.period_input)
        params_layout.addLayout(period_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Control Buttons
        control_layout = QHBoxLayout()

        self.acquire_btn = QPushButton('Start Acquisition')
        self.acquire_btn.clicked.connect(self.acquire_data)
        self.acquire_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D; /* Grey */
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        control_layout.addWidget(self.acquire_btn)

        self.stop_acquire_btn = QPushButton('Stop Acquisition')
        self.stop_acquire_btn.clicked.connect(self.stop_acquisition)
        self.stop_acquire_btn.setEnabled(False)
        self.stop_acquire_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545; /* Red */
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
            QPushButton:disabled {
                background-color: #adb5bd;
                color: #6c757d;
            }
        """)
        control_layout.addWidget(self.stop_acquire_btn)

        self.clear_btn = QPushButton('Clear Data')
        self.clear_btn.clicked.connect(self.clear_data)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107; /* Yellow */
                color: #212529;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        control_layout.addWidget(self.clear_btn)

        layout.addLayout(control_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel('Status: Ready to acquire.')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(self.status_label)

        # Plot
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Create subplots
        self.ax1 = self.figure.add_subplot(211)  # Voltage plot
        self.ax2 = self.figure.add_subplot(212)  # Resistance plot

        # Initialize plots
        self.line_voltage, = self.ax1.plot([], [], 'b-o', markersize=3, linewidth=1.5, label='Voltage')
        self.ax1.set_ylabel('Voltage (V)')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()

        self.line_resistance, = self.ax2.plot([], [], 'r-x', markersize=3, linewidth=1.5, label='Resistance')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Resistance (Ohm)')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend()

        self.figure.tight_layout()
        self.canvas.draw()

        self.setLayout(layout)

    def clear_data(self):
        """Clear all acquired data and reset the plot."""
        if self.is_acquiring:
            QMessageBox.warning(self, "Warning", "Cannot clear data while acquisition is running.")
            return

        self.data = pd.DataFrame(columns=['Time (s)', 'Voltage (V)', 'Resistance (Ohm)'])
        self.current_sample = 0

        # Clear plots
        self.line_voltage.set_data([], [])
        self.line_resistance.set_data([], [])

        # Reset axes
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        self.canvas.draw()
        self.status_label.setText('Status: Data cleared. Ready to acquire.')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")

    def acquire_data(self):
        """
        Starts the data acquisition process using a QTimer for live updates.
        """
        self.instrument = self.get_instrument()  # Get the current instrument instance
        if not self.instrument:
            QMessageBox.warning(self, "Connection Error",
                                "Instrument not connected. Please connect in 'Delta Mode Setup' tab.")
            return

        # Check if delta mode is active using the instrument's flag
        if not self.instrument.delta_mode_active:
            QMessageBox.warning(self, "Delta Mode Error",
                                "Delta Mode is not active. Please start Delta Mode in the 'Delta Mode Setup' tab first.")
            return

        self.num_samples_to_acquire = self.samples_input.value()
        self.measurement_period = self.period_input.value()

        # Reset acquisition state
        self.current_sample = 0
        self.start_time = time.time()
        self.is_acquiring = True

        # Setup progress bar
        self.progress_bar.setMaximum(self.num_samples_to_acquire)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.status_label.setText('Status: Acquiring data...')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #007BFF;")  # Blue for active

        # Update button states
        self.acquire_btn.setEnabled(False)
        self.stop_acquire_btn.setEnabled(True)
        self.samples_input.setEnabled(False)
        self.period_input.setEnabled(False)

        # Start the QTimer to call update_plot periodically
        self.timer.start(int(self.measurement_period * 1000))  # Period in milliseconds

    def stop_acquisition(self):
        """Stop the data acquisition."""
        self.timer.stop()
        self.is_acquiring = False

        # Update UI
        self.progress_bar.setVisible(False)
        self.acquire_btn.setEnabled(True)
        self.stop_acquire_btn.setEnabled(False)
        self.samples_input.setEnabled(True)
        self.period_input.setEnabled(True)

        self.status_label.setText(f'Status: Acquisition stopped. Acquired {self.current_sample} samples.')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;")

    def update_plot(self):
        """
        Reads a data point from the instrument, updates the plot, and checks
        if the acquisition is complete.
        """
        if not self.instrument:
            self.stop_acquisition()
            self.status_label.setText('Status: Error, instrument disconnected during acquisition.')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;")
            return

        if self.current_sample >= self.num_samples_to_acquire:
            self.timer.stop()
            self.is_acquiring = False
            self.progress_bar.setVisible(False)
            self.acquire_btn.setEnabled(True)
            self.stop_acquire_btn.setEnabled(False)
            self.samples_input.setEnabled(True)
            self.period_input.setEnabled(True)

            self.status_label.setText(f'Status: Acquisition complete. Acquired {self.current_sample} samples.')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #28A745;")
            return

        try:
            current_time = time.time() - self.start_time
            # Use the instrument's read_delta_data_point method
            voltage, resistance = self.instrument.read_delta_data_point()

            if voltage is not None or resistance is not None:
                new_row = {
                    'Time (s)': current_time,
                    'Voltage (V)': voltage if voltage is not None else float('nan'),
                    'Resistance (Ohm)': resistance if resistance is not None else float('nan')
                }
                self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)

                # Update voltage plot
                times_voltage = self.data['Time (s)'][self.data['Voltage (V)'].notna()]
                voltages_plot = self.data['Voltage (V)'][self.data['Voltage (V)'].notna()]
                if not voltages_plot.empty:
                    self.line_voltage.set_data(times_voltage, voltages_plot)
                    self.ax1.relim()
                    self.ax1.autoscale_view()

                # Update resistance plot
                times_resistance = self.data['Time (s)'][self.data['Resistance (Ohm)'].notna()]
                resistances_plot = self.data['Resistance (Ohm)'][self.data['Resistance (Ohm)'].notna()]
                if not resistances_plot.empty:
                    self.line_resistance.set_data(times_resistance, resistances_plot)
                    self.ax2.relim()
                    self.ax2.autoscale_view()

                self.canvas.draw()
                self.current_sample += 1

                # Update progress bar
                self.progress_bar.setValue(self.current_sample)

                # Update status based on the measurement mode
                status_text = f'Acquiring... {self.current_sample}/{self.num_samples_to_acquire}'
                if hasattr(self.instrument, 'voltage_mode'): # Check if attribute exists
                    if self.instrument.voltage_mode == 'V' and voltage is not None:
                        status_text += f' | V: {voltage:.6f}V'
                    elif self.instrument.voltage_mode == 'Ohm' and resistance is not None:
                        status_text += f' | R: {resistance:.6f}Ω'
                    else: # Fallback if mode is set but value is None
                        if voltage is not None:
                            status_text += f' | V: {voltage:.6f}V'
                        if resistance is not None:
                            status_text += f' | R: {resistance:.6f}Ω'
                else: # Fallback if voltage_mode attribute is missing
                    if voltage is not None:
                        status_text += f' | V: {voltage:.6f}V'
                    if resistance is not None:
                        status_text += f' | R: {resistance:.6f}Ω'


                self.status_label.setText(status_text)
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #007BFF;")
            else:
                # Handle case where no valid data was read
                self.status_label.setText(f'Warning: No data read at sample {self.current_sample + 1}. Continuing...')
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;")
                self.current_sample += 1 # Still increment sample count to avoid infinite loop

        except Exception as e:
            self.status_label.setText(f'Status: Error reading data: {e}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;")
            self.stop_acquisition()


class DeltaGUI(QTabWidget):
    """
    Main GUI application for Keithley 6221 Delta Mode.
    Manages the two tabs: Delta Mode Setup and Data Acquisition.
    """

    def __init__(self):
        super().__init__()
        self.instrument_instance = None  # This will hold the Keithley6221 object

        self.delta_tab = DeltaModeTab(get_instrument_callback=self.set_instrument_instance)
        self.data_tab = DataAcquisitionTab(get_instrument_callback=self.get_instrument_instance)

        self.addTab(self.delta_tab, 'Delta Mode Setup')
        self.addTab(self.data_tab, 'Data Acquisition')

        self.setWindowTitle('Keithley 6221 Delta Mode GUI')
        self.resize(800, 900)  # Increased size for better layout and plot visibility

        # Apply overall styling
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #f0f0f0;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
            QTabBar::tab:hover {
                background: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def set_instrument_instance(self, instrument):
        """Callback to set the instrument instance from the DeltaModeTab."""
        self.instrument_instance = instrument

    def get_instrument_instance(self):
        """Callback to get the instrument instance for the DataAcquisitionTab."""
        return self.instrument_instance

    def closeEvent(self, event):
        """Ensures the instrument connection is closed when the GUI window is closed."""
        if self.instrument_instance:
            try:
                # Stop data acquisition if running
                if hasattr(self.data_tab, 'is_acquiring') and self.data_tab.is_acquiring:
                    self.data_tab.stop_acquisition()

                # Stop delta mode if active and instrument has the attribute
                if hasattr(self.instrument_instance, 'delta_mode_active') and self.instrument_instance.delta_mode_active:
                    self.instrument_instance.stop_delta_mode()

                # Shutdown instrument connection via our unified driver's shutdown
                self.instrument_instance.shutdown()
                print("Instrument connection closed on GUI exit.")
            except Exception as e:
                print(f"Error closing instrument on exit: {e}")
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Keithley 6221 Delta Mode GUI")
    app.setApplicationVersion("1.0")

    gui = DeltaGUI()
    gui.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass


if __name__ == '__main__':
    main()