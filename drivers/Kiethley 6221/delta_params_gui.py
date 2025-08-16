import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGroupBox, QGridLayout, QLabel, QLineEdit, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

class IndicatorLight(QLabel):
    def __init__(self, diameter=20, parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)
        self.set_off()

    def set_on(self, color=QColor('red')):
        pixmap = QPixmap(self.diameter, self.diameter)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.black)
        painter.drawEllipse(0, 0, self.diameter-1, self.diameter-1)
        painter.end()
        self.setPixmap(pixmap)

    def set_off(self):
        pixmap = QPixmap(self.diameter, self.diameter)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('black'))
        painter.setPen(Qt.gray)
        painter.drawEllipse(0, 0, self.diameter-1, self.diameter-1)
        painter.end()
        self.setPixmap(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Delta Params In')
        self.compliance = False
        self.overflow = False
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Group box for Delta Params In
        self.delta_params_in_group = QGroupBox('Delta Params In')
        grid = QGridLayout()

        # High Level (A)
        self.high_level_a_label = QLabel('High Level (A)')
        self.high_level_a = QLineEdit('0.0001')
        grid.addWidget(self.high_level_a_label, 0, 0)
        grid.addWidget(self.high_level_a, 0, 1)

        # Low Level (A)
        self.low_level_a_label = QLabel('Low Level (A)')
        self.low_level_a = QLineEdit('-0.0001')
        grid.addWidget(self.low_level_a_label, 1, 0)
        grid.addWidget(self.low_level_a, 1, 1)

        # Compliance (V)
        self.compliance_v_label = QLabel('Compliance (V)')
        self.compliance_v = QLineEdit('1')
        grid.addWidget(self.compliance_v_label, 2, 0)
        grid.addWidget(self.compliance_v, 2, 1)

        # 2182A Range
        self.range_2182a_label = QLabel('2182A Range')
        self.range_2182a = QComboBox()
        self.range_2182a.addItems(['10mV', '100mV', '1V', '10V', '100V'])
        grid.addWidget(self.range_2182a_label, 3, 0)
        grid.addWidget(self.range_2182a, 3, 1)

        # Init When Armed
        self.init_when_armed = QCheckBox('Init When Armed')
        self.init_when_armed.setChecked(True)
        grid.addWidget(self.init_when_armed, 4, 0, 1, 2)

        # Meas Units
        self.meas_units_label = QLabel('Meas Units')
        self.meas_units = QComboBox()
        self.meas_units.addItems(['Volts', 'Ohms'])
        grid.addWidget(self.meas_units_label, 5, 0)
        grid.addWidget(self.meas_units, 5, 1)

        # Delay (s)
        self.delay_s_label = QLabel('Delay (s)')
        self.delay_s = QLineEdit('0.002')
        grid.addWidget(self.delay_s_label, 6, 0)
        grid.addWidget(self.delay_s, 6, 1)

        # Abort On Compliance
        self.abort_on_compliance = QCheckBox('Abort On Compliance?')
        grid.addWidget(self.abort_on_compliance, 7, 0, 1, 2)

        self.delta_params_in_group.setLayout(grid)
        main_layout.addWidget(self.delta_params_in_group)

        # Status/Diagnostics section for indicator lights
        status_group = QGroupBox('Status')
        status_layout = QHBoxLayout()
        # Compliance indicator
        self.compliance_label = QLabel('Compliance')
        self.compliance_light = IndicatorLight()
        status_layout.addWidget(self.compliance_label)
        status_layout.addWidget(self.compliance_light)
        # Overflow indicator
        self.overflow_label = QLabel('Overflow')
        self.overflow_light = IndicatorLight()
        status_layout.addWidget(self.overflow_label)
        status_layout.addWidget(self.overflow_light)
        status_layout.addStretch(1)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Placeholder for future connections
        self.connect_signals()
        self.update_indicators()

    def connect_signals(self):
        # Connect signals to dummy functions
        self.high_level_a.textChanged.connect(self.on_high_level_a_changed)
        self.low_level_a.textChanged.connect(self.on_low_level_a_changed)
        self.compliance_v.textChanged.connect(self.on_compliance_v_changed)
        self.range_2182a.currentIndexChanged.connect(self.on_range_2182a_changed)
        self.init_when_armed.stateChanged.connect(self.on_init_when_armed_changed)
        self.meas_units.currentIndexChanged.connect(self.on_meas_units_changed)
        self.delay_s.textChanged.connect(self.on_delay_s_changed)
        self.abort_on_compliance.stateChanged.connect(self.on_abort_on_compliance_changed)

    def update_indicators(self):
        if self.compliance:
            self.compliance_light.set_on()
        else:
            self.compliance_light.set_off()
        if self.overflow:
            self.overflow_light.set_on()
        else:
            self.overflow_light.set_off()

    # Dummy slot functions
    def on_high_level_a_changed(self, value):
        pass
    def on_low_level_a_changed(self, value):
        pass
    def on_compliance_v_changed(self, value):
        pass
    def on_range_2182a_changed(self, idx):
        pass
    def on_init_when_armed_changed(self, state):
        pass
    def on_meas_units_changed(self, idx):
        pass
    def on_delay_s_changed(self, value):
        pass
    def on_abort_on_compliance_changed(self, state):
        pass

    # Example methods to set indicator status
    def set_compliance(self, value: bool):
        self.compliance = value
        self.update_indicators()

    def set_overflow(self, value: bool):
        self.overflow = value
        self.update_indicators()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 