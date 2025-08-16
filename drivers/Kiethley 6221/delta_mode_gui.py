import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QComboBox, QPushButton, 
                             QFormLayout, QGroupBox, QMessageBox, QDoubleSpinBox, 
                             QSpinBox, QCheckBox)
from pymeasure.instruments.keithley import Keithley6221

class DeltaModeGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keithley = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Keithley 6221 Delta Mode")
        self.setup_ui_components()
        self.setup_layout()
        self.is_connected = False
        
    def setup_ui_components(self):
        # Connection components
        self.connection_status = QLabel("Not Connected")
        self.gpib_address = QLineEdit("25")
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # Delta parameters
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["V", "Ohms", "W", "Siemens"])
        
        self.high_source = QDoubleSpinBox()
        self.high_source.setRange(0, 0.105)
        self.high_source.setValue(0.01)
        self.high_source.valueChanged.connect(self.update_low_source)
        
        self.low_source = QDoubleSpinBox()
        self.low_source.setRange(-0.105, 0)
        self.low_source.setValue(-0.01)
        self.low_source.setEnabled(False)
        
        self.delay = QDoubleSpinBox()
        self.delay.setRange(0, 9999.999)
        self.delay.setValue(1.0)
        
        self.cycles_combo = QComboBox()
        self.cycles_combo.addItems(["INF", "Custom"])
        self.cycles_combo.currentIndexChanged.connect(self.toggle_cycles_custom)
        
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 65536)
        self.cycles_spin.setValue(100)
        self.cycles_spin.setEnabled(False)
        
        self.compliance_abort = QCheckBox()
        self.compliance_abort.setChecked(True)
        
        self.buffer_points = QSpinBox()
        self.buffer_points.setRange(1, 1000000)
        self.buffer_points.setValue(1000)
        
        # Control buttons
        self.arm_btn = QPushButton("Arm")
        self.arm_btn.clicked.connect(self.arm_delta)
        self.arm_btn.setEnabled(False)
        
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_delta)
        self.start_btn.setEnabled(False)
        
        self.abort_btn = QPushButton("Abort")
        self.abort_btn.clicked.connect(self.abort_delta)
        self.abort_btn.setEnabled(False)
        
        self.status_display = QLabel("Ready to connect...")
        self.status_display.setStyleSheet("QLabel { color: gray; }")
        
    def setup_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("GPIB Address:"))
        conn_layout.addWidget(self.gpib_address)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addWidget(self.connection_status)
        conn_group.setLayout(conn_layout)
        
        # Parameters group
        params_group = QGroupBox("Delta Mode Parameters")
        params_layout = QFormLayout()
        
        cycles_layout = QHBoxLayout()
        cycles_layout.addWidget(self.cycles_combo)
        cycles_layout.addWidget(self.cycles_spin)
        
        params_layout.addRow("Unit:", self.unit_combo)
        params_layout.addRow("High Source (A):", self.high_source)
        params_layout.addRow("Low Source (A):", self.low_source)
        params_layout.addRow("Delay (s):", self.delay)
        params_layout.addRow("Cycles:", cycles_layout)
        params_layout.addRow("Compliance Abort:", self.compliance_abort)
        params_layout.addRow("Buffer Points:", self.buffer_points)
        params_group.setLayout(params_layout)
        
        # Control buttons layout
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.arm_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.abort_btn)
        
        # Add all to main layout
        layout.addWidget(conn_group)
        layout.addWidget(params_group)
        layout.addLayout(control_layout)
        layout.addWidget(self.status_display)
        
    def toggle_cycles_custom(self, index):
        self.cycles_spin.setEnabled(index == 1)
    
    def update_low_source(self, value):
        self.low_source.setValue(-value)
    
    def toggle_connection(self):
        if not self.is_connected:
            try:
                gpib_address = int(self.gpib_address.text().strip())
                self.keithley = Keithley6221(f"GPIB::{gpib_address}")
                self.keithley.reset()
                self.is_connected = True
                self.connection_status.setText("Connected")
                self.connection_status.setStyleSheet("color: green;")
                self.connect_btn.setText("Disconnect")
                self.arm_btn.setEnabled(True)
                self.update_status("Connected to Keithley 6221")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")
        else:
            self.disconnect_instrument()
    
    def disconnect_instrument(self):
        if self.keithley:
            try:
                self.keithley.shutdown()
            except:
                pass
            self.keithley = None
        self.is_connected = False
        self.connection_status.setText("Not Connected")
        self.connection_status.setStyleSheet("color: red;")
        self.connect_btn.setText("Connect")
        self.arm_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.abort_btn.setEnabled(False)
        self.update_status("Disconnected")
    
    def arm_delta(self):
        if not self.is_connected:
            return
            
        try:
            self.keithley.delta_unit = self.unit_combo.currentText()
            self.keithley.delta_high_source = self.high_source.value()
            self.keithley.delta_low_source = self.low_source.value()
            self.keithley.delta_delay = self.delay.value()
            self.keithley.delta_cycles = self.cycles_spin.value() if self.cycles_combo.currentIndex() == 1 else "INF"
            self.keithley.delta_compliance_abort_enabled = self.compliance_abort.isChecked()
            self.keithley.delta_buffer_points = self.buffer_points.value()
            self.keithley.delta_arm()
            self.start_btn.setEnabled(True)
            self.abort_btn.setEnabled(True)
            self.update_status("Delta mode armed")
        except Exception as e:
            self.update_status(f"Arm failed: {str(e)}", "red")
    
    def start_delta(self):
        try:
            self.keithley.delta_start()
            self.update_status("Delta measurements started")
        except Exception as e:
            self.update_status(f"Start failed: {str(e)}", "red")
    
    def abort_delta(self):
        try:
            self.keithley.delta_abort()
            self.update_status("Delta measurements aborted")
        except Exception as e:
            self.update_status(f"Abort failed: {str(e)}", "red")
    
    def update_status(self, message, color="black"):
        self.status_display.setText(message)
        self.status_display.setStyleSheet(f"QLabel {{ color: {color}; }}")

def main():
    app = QApplication(sys.argv)
    window = DeltaModeGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
