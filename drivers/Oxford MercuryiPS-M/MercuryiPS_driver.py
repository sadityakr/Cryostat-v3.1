"""
Oxford Instruments Mercury iPS-M Magnet Power Supply Driver

This module provides a Python interface to control the Oxford Instruments 
Mercury iPS-M magnet power supply using SCPI commands.

Author: Generated for Cryostat-v3
Date: 2024
"""

import socket
import time
import logging
from typing import Optional, Union, Dict, Any
from enum import Enum

try:
    import pyvisa as visa
except ImportError:
    raise ImportError("PyVISA is required. Install it with: pip install pyvisa")


class ConnectionMode(Enum):
    """Connection modes for the Mercury iPS-M"""
    IP = "ip"
    VISA = "visa"


class MagnetStatus(Enum):
    """Magnet status enumeration"""
    HOLD = "HOLD"
    RAMPING_TO_SET = "RTOS"
    RAMPING_TO_ZERO = "RTOZ"
    CLAMPED = "CLMP"
    UNKNOWN = "UNKNOWN"


class MercuryiPSDriver:
    """
    Driver for Oxford Instruments Mercury iPS-M Magnet Power Supply
    
    This driver provides a high-level interface to control the magnet power supply
    using SCPI commands over either IP or VISA connections.
    """
    
    def __init__(self, mode: str = "ip", resource_name: Optional[str] = None, 
                 ip_address: Optional[str] = None, port: int = 7020, 
                 timeout: float = 10.0, bytes_to_read: int = 2048):
        """
        Initialize the Mercury iPS-M driver
        
        Args:
            mode: Connection mode ('ip' or 'visa')
            resource_name: VISA resource name (for VISA mode)
            ip_address: IP address (for IP mode)
            port: Port number (for IP mode)
            timeout: Communication timeout in seconds
            bytes_to_read: Number of bytes to read from responses
        """
        self.mode = ConnectionMode(mode.lower())
        self.resource_name = resource_name
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.bytes_to_read = bytes_to_read
        self.connected = False
        self.resource_manager = None
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize VISA resource manager if needed
        if self.mode == ConnectionMode.VISA:
            self.resource_manager = visa.ResourceManager()
    
    def connect(self) -> bool:
        """
        Establish connection to the Mercury iPS-M and verify communication
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Send *IDN? query to verify communication
            response = self._query("*IDN?")
            if response and "OXFORD INSTRUMENTS:MERCURY" in response:
                self.connected = True
                self.logger.info(f"Successfully connected to Mercury iPS-M: {response}")
                return True
            else:
                self.logger.error("Invalid response to *IDN? query")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Close the connection to the Mercury iPS-M"""
        self.connected = False
        self.logger.info("Disconnected from Mercury iPS-M")
    
    def _query(self, command: str) -> Optional[str]:
        """
        Send a query command and return the response
        
        Args:
            command: SCPI command to send
            
        Returns:
            str: Response from the device, or None if error
        """
        if not self.connected and command != "*IDN?":
            self.logger.error("Not connected to device")
            return None
        
        try:
            if self.mode == ConnectionMode.IP:
                return self._query_ip(command)
            else:
                return self._query_visa(command)
        except Exception as e:
            self.logger.error(f"Query failed for command '{command}': {e}")
            return None
    
    def _query_ip(self, command: str) -> Optional[str]:
        """Send query via IP connection"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip_address, self.port))
            s.settimeout(self.timeout)
            # Add newline to command if not present
            if not command.endswith('\n'):
                command += '\n'
            s.sendall(command.encode())
            response = s.recv(self.bytes_to_read).decode()
            return response.strip()
    
    def _query_visa(self, command: str) -> Optional[str]:
        """Send query via VISA connection"""
        instr = self.resource_manager.open_resource(self.resource_name)
        instr.timeout = int(self.timeout * 1000)  # Convert to milliseconds
        response = instr.query(command)
        instr.close()
        return response.strip()
    
    def _set(self, command: str) -> bool:
        """
        Send a set command
        
        Args:
            command: SCPI command to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to device")
            return False
        
        try:
            response = self._query(command)
            # For set commands, any response indicates success
            if response:
                self.logger.info(f"Set command successful: {command}")
                return True
            else:
                self.logger.error(f"Set command failed: {command}")
                return False
        except Exception as e:
            self.logger.error(f"Set command failed for '{command}': {e}")
            return False
    
    def _extract_value(self, response: str, noun: str, unit: str) -> Optional[float]:
        """
        Extract numeric value from response using the same logic as mercuryips.py
        
        Args:
            response: Response from device
            noun: The NOUN part of the command (e.g., 'DEV:GRPZ:PSU:SIG:FLD')
            unit: The unit to remove (e.g., 'T', 'A', 'V')
            
        Returns:
            float: Extracted value, or None if parsing fails
        """
        try:
            expected_response = 'STAT:' + noun + ':'
            if response.startswith(expected_response):
                # Remove the expected prefix and unit, then convert to float
                value_str = response.replace(expected_response, '').strip('\n').replace(unit, '')
                return float(value_str)
            else:
                self.logger.error(f"Unexpected response format: {response}")
                return None
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Failed to parse value from response '{response}': {e}")
            return None
    
    def read_current(self) -> Optional[float]:
        """
        Read the current through the magnet leads
        
        Returns:
            float: Current in Amperes, or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:CURR?")
        if response:
            return self._extract_value(response, "DEV:GRPZ:PSU:SIG:CURR", "A")
        return None
    
    def set_current(self, value: float) -> bool:
        """
        Set the target current
        
        Args:
            value: Target current in Amperes
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check current limits based on documentation (CLIM parameter)
        # Using a conservative limit of 360A based on the SCPI documentation
        if abs(value) > 360.0:
            self.logger.warning(f"Current value {value}A exceeds 360A limit")
            return False
        
        command = f"SET:DEV:GRPZ:PSU:SIG:CSET:{value}"
        return self._set(command)
    
    def set_current_ramp_rate(self, rate: float) -> bool:
        """
        Set the current ramp rate
        
        Args:
            rate: Ramp rate in Amperes/min
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check rate limits based on documentation (RCST parameter)
        if rate < 0.0 or rate > 1200.0:
            self.logger.warning(f"Current ramp rate {rate} A/min is outside valid range (0-1200 A/min)")
            return False
        
        command = f"SET:DEV:GRPZ:PSU:SIG:RCST:{rate}"
        return self._set(command)
    
    def read_current_ramp_rate(self) -> Optional[float]:
        """
        Read the current ramp rate
        
        Returns:
            float: Ramp rate in Amperes/min, or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:RCST?")
        if response:
            return self._extract_value(response, "DEV:GRPZ:PSU:SIG:RCST", "A/m")
        return None
    
    def read_current_setpoint(self) -> Optional[float]:
        """
        Read the current setpoint
        
        Returns:
            float: Current setpoint in Amperes, or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:CSET?")
        if response:
            return self._extract_value(response, "DEV:GRPZ:PSU:SIG:CSET", "A")
        return None
    
    def switch_heater_on(self) -> bool:
        """
        Turn the superconducting switch heater on
        
        Returns:
            bool: True if successful, False otherwise
        """
        command = "SET:DEV:GRPZ:PSU:SIG:SWHN:ON"
        return self._set(command)
    
    def switch_heater_off(self) -> bool:
        """
        Turn the superconducting switch heater off
        
        Returns:
            bool: True if successful, False otherwise
        """
        command = "SET:DEV:GRPZ:PSU:SIG:SWHN:OFF"
        return self._set(command)
    
    def read_switch_heater_status(self) -> Optional[str]:
        """
        Read the switch heater status
        
        Returns:
            str: "ON", "OFF", or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:SWHT?")
        if response and "STAT:" in response:
            try:
                # Extract status from response like "STAT:DEV:GRPZ:PSU:SIG:SWHT:ON"
                status = response.split(":")[-1].strip()
                return status
            except IndexError as e:
                self.logger.error(f"Failed to parse switch heater status: {e}")
                return None
        return None
    
    def set_field_zero(self) -> bool:
        """
        Ramp the field safely to zero
        
        Returns:
            bool: True if successful, False otherwise
        """
        command = "SET:DEV:GRPZ:PSU:ACTN:RTOZ"
        return self._set(command)
    
    def hold_field(self) -> bool:
        """
        Hold the current field
        
        Returns:
            bool: True if successful, False otherwise
        """
        command = "SET:DEV:GRPZ:PSU:ACTN:HOLD"
        return self._set(command)
    
    def ramp_to_setpoint(self) -> bool:
        """
        Ramp the field to the current setpoint
        
        Returns:
            bool: True if successful, False otherwise
        """
        command = "SET:DEV:GRPZ:PSU:ACTN:RTOS"
        return self._set(command)
    
    def read_magnet_status(self) -> MagnetStatus:
        """
        Read the magnet status
        
        Returns:
            MagnetStatus: Current magnet status
        """
        response = self._query("READ:DEV:GRPZ:PSU:ACTN?")
        if response and "STAT:" in response:
            try:
                status = response.split(":")[-1].strip()
                return MagnetStatus(status)
            except (IndexError, ValueError) as e:
                self.logger.error(f"Failed to parse magnet status: {e}")
                return MagnetStatus.UNKNOWN
        return MagnetStatus.UNKNOWN
    
    def read_persistent_current(self) -> Optional[float]:
        """
        Read the persistent current
        
        Returns:
            float: Persistent current in Amperes, or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:PCUR?")
        if response:
            return self._extract_value(response, "DEV:GRPZ:PSU:SIG:PCUR", "A")
        return None
    
    def read_voltage(self) -> Optional[float]:
        """
        Read the voltage across the magnet
        
        Returns:
            float: Voltage in Volts, or None if error
        """
        response = self._query("READ:DEV:GRPZ:PSU:SIG:VOLT?")
        if response:
            return self._extract_value(response, "DEV:GRPZ:PSU:SIG:VOLT", "V")
        return None
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information
        
        Returns:
            dict: Device information including IDN, configuration, etc.
        """
        info = {}
        
        # Get device identification
        idn_response = self._query("*IDN?")
        if idn_response:
            info['identification'] = idn_response
        
        # Get system configuration
        cat_response = self._query("READ:SYS:CAT?")
        if cat_response:
            info['configuration'] = cat_response
        
        return info
    
    def is_connected(self) -> bool:
        """
        Check if connected to the device
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected


# Mock driver for testing without hardware
class MockMercuryiPSDriver(MercuryiPSDriver):
    """
    Mock driver for testing without actual hardware
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_current = 0.0
        self._mock_current_ramp_rate = 1.0
        self._mock_current_setpoint = 0.0
        self._mock_heater_status = "OFF"
        self._mock_magnet_status = MagnetStatus.HOLD
        self._mock_persistent_current = 0.0
        self._mock_voltage = 0.0
    
    def connect(self) -> bool:
        """Mock connection - always succeeds"""
        self.connected = True
        self.logger.info("Mock connection established")
        return True
    
    def _query(self, command: str) -> Optional[str]:
        """Mock query responses"""
        if command == "*IDN?":
            return "STAT:OXFORD INSTRUMENTS:MERCURY iPS:12345:1.0"
        elif command == "READ:DEV:GRPZ:PSU:SIG:CURR?":
            return f"STAT:DEV:GRPZ:PSU:SIG:CURR:{self._mock_current}:A"
        elif command == "READ:DEV:GRPZ:PSU:SIG:RCST?":
            return f"STAT:DEV:GRPZ:PSU:SIG:RCST:{self._mock_current_ramp_rate}:A/m"
        elif command == "READ:DEV:GRPZ:PSU:SIG:CSET?":
            return f"STAT:DEV:GRPZ:PSU:SIG:CSET:{self._mock_current_setpoint}:A"
        elif command == "READ:DEV:GRPZ:PSU:SIG:SWHT?":
            return f"STAT:DEV:GRPZ:PSU:SIG:SWHT:{self._mock_heater_status}"
        elif command == "READ:DEV:GRPZ:PSU:ACTN?":
            return f"STAT:DEV:GRPZ:PSU:ACTN:{self._mock_magnet_status.value}"
        elif command == "READ:DEV:GRPZ:PSU:SIG:PCUR?":
            return f"STAT:DEV:GRPZ:PSU:SIG:PCUR:{self._mock_persistent_current}:A"
        elif command == "READ:DEV:GRPZ:PSU:SIG:VOLT?":
            return f"STAT:DEV:GRPZ:PSU:SIG:VOLT:{self._mock_voltage}:V"
        elif command == "READ:SYS:CAT?":
            return "STAT:DEV:MB0:TEMP:DEV:GRPZ:PSU"
        else:
            return "STAT:OK"
    
    def _set(self, command: str) -> bool:
        """Mock set commands"""
        if "CSET:" in command:
            try:
                value = float(command.split(":")[-1])
                self._mock_current_setpoint = value
                return True
            except ValueError:
                return False
        elif "RCST:" in command:
            try:
                value = float(command.split(":")[-1])
                self._mock_current_ramp_rate = value
                return True
            except ValueError:
                return False
        elif "SWHN:ON" in command:
            self._mock_heater_status = "ON"
            return True
        elif "SWHN:OFF" in command:
            self._mock_heater_status = "OFF"
            return True
        elif "ACTN:RTOZ" in command:
            self._mock_magnet_status = MagnetStatus.RAMPING_TO_ZERO
            return True
        elif "ACTN:HOLD" in command:
            self._mock_magnet_status = MagnetStatus.HOLD
            return True
        elif "ACTN:RTOS" in command:
            self._mock_magnet_status = MagnetStatus.RAMPING_TO_SET
            return True
        else:
            return True 