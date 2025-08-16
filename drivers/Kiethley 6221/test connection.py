import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
import pyvisa
from pymeasure.instruments.keithley import Keithley6221

class KeithleyConnectionCheckerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.instrument = None
        self.resource = None
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface elements."""
        self.setWindowTitle('Keithley 6221 Connection Checker')
        self.setGeometry(100, 100, 500, 200) # x, y, width, height

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10) # Add some spacing between widgets

        # VISA Address Input
        address_layout = QHBoxLayout()
        address_label = QLabel('VISA Address:')
        address_label.setFixedWidth(100) # Fixed width for label for alignment
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., GPIB0::10::INSTR or USB0::0x05E6::0x6221::01234567::INSTR")
        self.address_input.setText("GPIB0::19::INSTR") # Set default address here
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_input)
        main_layout.addLayout(address_layout)

        # Test Connection Button
        self.test_button = QPushButton('Test Connection')
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green */
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
                box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        main_layout.addWidget(self.test_button, alignment=Qt.AlignCenter)

        # Status Label
        self.status_label = QLabel('Status: Not connected')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.status_label.setWordWrap(True) # Allow text to wrap
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

    def test_connection(self):
        """
        Attempts to connect to the Keithley 6221 and query its IDN.
        Updates the status label with the result.
        """
        visa_address = self.address_input.text().strip()
        if not visa_address:
            QMessageBox.warning(self, "Input Error", "Please enter a VISA address.")
            return

        self.status_label.setText('Status: Attempting to connect...')
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA500;") # Orange for pending

        # Ensure previous connections are closed before attempting a new one
        self._close_connection()

        try:
            # Initialize the PyVISA ResourceManager
            rm = pyvisa.ResourceManager()
            # Open the VISA resource
            self.resource = rm.open_resource(visa_address)
            # Set a timeout for the VISA resource (in milliseconds)
            self.resource.timeout = 5000  # 5 seconds, adjust as needed

            # Instantiate the Keithley6221 instrument using pymeasure
            self.instrument = Keithley6221(self.resource)

            # Perform an IDN query using the pymeasure instrument's 'ask' method.
            idn = self.instrument.ask("*IDN?")
            self.status_label.setText(f'Status: Connected!\nInstrument IDN: {idn.strip()}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #28A745;") # Green for success

        except pyvisa.errors.VisaIOError as e:
            self.status_label.setText(
                f'Status: Connection Error!\n'
                f'Could not connect to {visa_address}.\n'
                f'Please ensure the instrument is powered on, connected, and the VISA address is correct.\n'
                f'Error details: {e}'
            )
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;") # Red for error
        except Exception as e:
            self.status_label.setText(f'Status: An unexpected error occurred: {e}')
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC3545;") # Red for error
        finally:
            # The connection is kept open if successful for potential future operations,
            # but will be closed if a new test is initiated or the app closes.
            pass

    def _close_connection(self):
        """Helper to close any open instrument or resource connections."""
        if self.instrument:
            try:
                self.instrument.shutdown()
            except Exception as e:
                print(f"Error during instrument shutdown: {e}")
            self.instrument = None
        if self.resource:
            try:
                self.resource.close()
            except Exception as e:
                print(f"Error during resource close: {e}")
            self.resource = None

    def closeEvent(self, event):
        """Ensures the connection is closed when the GUI window is closed."""
        self._close_connection()
        event.accept()

def main():
    app = QApplication(sys.argv)
    gui = KeithleyConnectionCheckerGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
