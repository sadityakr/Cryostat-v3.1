# Oxford Instruments Mercury iPS-M Magnet Power Supply Driver

This package provides a Python driver and GUI for controlling the Oxford Instruments Mercury iPS-M magnet power supply using SCPI commands.

## Features

- **Complete SCPI Command Support**: Implements all major SCPI commands from the Oxford Instruments documentation
- **Dual Connection Modes**: Support for both IP (Ethernet) and VISA (GPIB/USB) connections
- **Comprehensive GUI**: Full-featured graphical user interface with real-time monitoring
- **Mock Driver**: Test functionality without actual hardware
- **Robust Error Handling**: Comprehensive error handling and logging
- **Thread-Safe**: GUI updates run in separate thread for responsive interface

## Files

- `MercuryiPS_driver.py` - Main driver implementation
- `MercuryiPS_gui.py` - Graphical user interface
- `test_driver.py` - Test script for driver functionality
- `README.md` - This documentation file

## Installation

### Prerequisites

```bash
pip install pyvisa qcodes tkinter
```

### For VISA Support (Windows)
```bash
pip install pyvisa-py
```

### For VISA Support (Linux)
```bash
sudo apt-get install libusb-1.0-0-dev
pip install pyvisa-py
```

## Usage

### Running the GUI

#### With Real Hardware
```bash
python MercuryiPS_gui.py
```

#### With Mock Driver (for testing)
```bash
python MercuryiPS_gui.py --mock
```

### Running the Test Script
```bash
python test_driver.py
```

### Using the Driver in Your Code

```python
from MercuryiPS_driver import MercuryiPSDriver

# Create driver instance
driver = MercuryiPSDriver(mode="ip", ip_address="192.168.1.100", port=7020)

# Connect to device
if driver.connect():
    print("Connected successfully!")
    
    # Read current field
    field = driver.read_field()
    print(f"Current field: {field} T")
    
    # Set field
    driver.set_field(5.0)
    
    # Set ramp rate
    driver.set_ramp_rate(2.5)
    
    # Disconnect
    driver.disconnect()
```

## API Documentation

### MercuryiPSDriver Class

#### Constructor
```python
MercuryiPSDriver(mode="ip", resource_name=None, ip_address=None, port=7020, timeout=10.0, bytes_to_read=2048)
```

**Parameters:**
- `mode` (str): Connection mode - "ip" or "visa"
- `resource_name` (str): VISA resource name (for VISA mode)
- `ip_address` (str): IP address (for IP mode)
- `port` (int): Port number (for IP mode, default: 7020)
- `timeout` (float): Communication timeout in seconds
- `bytes_to_read` (int): Number of bytes to read from responses

#### Methods

##### Connection Management
- `connect()` → bool: Establish connection and verify communication
- `disconnect()`: Close connection
- `is_connected()` → bool: Check connection status

##### Field Control
- `read_field()` → Optional[float]: Read current magnetic field (Tesla)
- `set_field(value: float)` → bool: Set target magnetic field (Tesla)
- `set_ramp_rate(rate: float)` → bool: Set field ramp rate (Tesla/min)
- `read_ramp_rate()` → Optional[float]: Read current ramp rate (Tesla/min)

##### Magnet Control
- `set_field_zero()` → bool: Ramp field safely to zero
- `hold_field()` → bool: Hold current field
- `read_magnet_status()` → MagnetStatus: Read magnet status

##### Switch Heater Control
- `switch_heater_on()` → bool: Turn superconducting switch heater on
- `switch_heater_off()` → bool: Turn switch heater off
- `read_switch_heater_status()` → Optional[str]: Read heater status ("ON"/"OFF")

##### Monitoring
- `read_lead_current()` → Optional[float]: Read current through magnet leads (A)
- `read_persistent_current()` → Optional[float]: Read persistent current (A)
- `read_voltage()` → Optional[float]: Read voltage across magnet (V)

##### Device Information
- `get_device_info()` → Dict[str, Any]: Get device identification and configuration

### MagnetStatus Enum
```python
class MagnetStatus(Enum):
    HOLD = "HOLD"                    # Magnet holding current field
    RAMPING_TO_SET = "RTOS"         # Ramping to setpoint
    RAMPING_TO_ZERO = "RTOZ"        # Ramping to zero
    CLAMPED = "CLMP"                # Output clamped
    UNKNOWN = "UNKNOWN"             # Unknown status
```

### MockMercuryiPSDriver Class

The mock driver provides the same interface as the real driver but simulates responses for testing without hardware.

## GUI Features

### Connection Panel
- Connection mode selection (IP/VISA)
- IP address and port configuration
- VISA resource name input
- Connect/Disconnect buttons
- Connection status indicator

### Field Control Panel
- Real-time field display
- Field setpoint input
- Ramp rate input and display
- Set field and ramp rate buttons

### Control Panel
- Ramp to zero button
- Hold field button
- Switch heater on/off buttons
- Real-time status monitoring

### Status Panel
- Magnet status display
- Lead current monitoring
- Persistent current monitoring
- Voltage monitoring
- Switch heater status

### Log Panel
- Real-time log messages
- Clear log functionality
- Error and warning display

## SCPI Commands Implemented

The driver implements the following SCPI commands from the Oxford Instruments documentation:

### Device Identification
- `*IDN?` - Device identification

### System Commands
- `READ:SYS:CAT?` - System configuration

### Magnet Control (GRPZ axis)
- `READ:DEV:GRPZ:PSU:SIG:FLD?` - Read magnetic field
- `SET:DEV:GRPZ:PSU:SIG:FSET:<value>` - Set field setpoint
- `READ:DEV:GRPZ:PSU:SIG:RFST?` - Read field ramp rate
- `SET:DEV:GRPZ:PSU:SIG:RFST:<value>` - Set field ramp rate
- `READ:DEV:GRPZ:PSU:SIG:CURR?` - Read lead current
- `READ:DEV:GRPZ:PSU:SIG:PCUR?` - Read persistent current
- `READ:DEV:GRPZ:PSU:SIG:VOLT?` - Read voltage
- `READ:DEV:GRPZ:PSU:SIG:SWHT?` - Read switch heater status
- `SET:DEV:GRPZ:PSU:SIG:SWHN:ON` - Turn switch heater on
- `SET:DEV:GRPZ:PSU:SIG:SWHN:OFF` - Turn switch heater off
- `READ:DEV:GRPZ:PSU:ACTN?` - Read magnet action status
- `SET:DEV:GRPZ:PSU:ACTN:RTOZ` - Ramp to zero
- `SET:DEV:GRPZ:PSU:ACTN:HOLD` - Hold field

## Safety Features

### Field Limits
- Maximum field: 12 Tesla (4.2K operation)
- Field range validation before setting

### Ramp Rate Limits
- Maximum ramp rate: 50 Tesla/min
- Rate validation before setting

### Error Handling
- Connection timeout handling
- Invalid command responses
- Communication error recovery
- User confirmation for critical operations

## Testing

### Mock Driver Testing
The mock driver allows testing of all functionality without hardware:

```python
from MercuryiPS_driver import MockMercuryiPSDriver

# Create mock driver
driver = MockMercuryiPSDriver()

# Test all functions
driver.connect()
field = driver.read_field()
driver.set_field(5.0)
# ... etc
```

### GUI Testing
Run the GUI with mock mode:
```bash
python MercuryiPS_gui.py --mock
```

## Troubleshooting

### Connection Issues
1. **IP Connection**: Verify IP address and port (default: 7020)
2. **VISA Connection**: Check VISA resource name and driver installation
3. **Timeout**: Increase timeout value for slow connections

### PyVISA Issues
1. **Windows**: Install NI-VISA or pyvisa-py
2. **Linux**: Install libusb and pyvisa-py
3. **Resource not found**: Use `pyvisa.ResourceManager().list_resources()` to find available resources

### GUI Issues
1. **Not responding**: Check if update thread is running
2. **Connection errors**: Verify device is powered on and accessible
3. **Display not updating**: Check if device is connected

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the GNU General Public License v2.0.

## References

- Oxford Instruments Mercury iPS-M SCPI Command Reference
- PyVISA Documentation: https://pyvisa.readthedocs.io/
- QCoDeS Documentation: https://qcodes.github.io/Qcodes/

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test script for examples
3. Check the log output for error messages
4. Verify SCPI command documentation 