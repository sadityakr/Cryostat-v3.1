from pymeasure.instruments import Instrument
from pymeasure.adapters import VISAAdapter
import time
import pyvisa

class OI_ILM_210(Instrument):
    def __init__(self, adapter, name="OI ILM 210", **kwargs):
        super().__init__(adapter, name, **kwargs)
        
        # Set VISA attributes for serial communication
        try:
            self.adapter.connection.set_visa_attribute(pyvisa.constants.VI_ATTR_ASRL_STOP_BITS, 
                                                    pyvisa.constants.VI_ASRL_STOP_TWO)
        except Exception as e:
            print(f"Could not set VISA attributes: {e}")
        
        self._number = 1  # ISOBUS instrument number
        
        # Initialize instrument
        self._initialize()
    
    def _initialize(self):
        """Initialize the instrument to a known state."""
        try:
            self.get_idn()
            time.sleep(0.07)  # wait for device to respond
        except Exception as e:
            print(f"Initial communication failed: {e}")
    
    def _execute(self, message):
        """Execute command with ISOBUS addressing."""
        try:
            # Add ISOBUS instrument number prefix
            command = f"@{self._number}{message}"
            self.write(command)
            time.sleep(0.07)  # wait for device to respond
            return self.read()
        except Exception as e:
            print(f"Communication error: {e}")
            return None
    
    def get_idn(self):
        """Get instrument identification."""
        try:
            version_response = self._get_version()
            if version_response:
                idstr = version_response.split()
                if len(idstr) >= 6:
                    idparts = [idstr[3] + ' ' + idstr[4], idstr[0], idstr[5],
                               idstr[1] + ' ' + idstr[2]]
                else:
                    idparts = [None, None, None, None]
                if len(idparts) < 4:
                    idparts += [None] * (4 - len(idparts))
            else:
                idparts = [None, None, None, None]
            
            return dict(zip(('vendor', 'model', 'serial', 'firmware'), idparts))
        except Exception as e:
            print(f'Error getting IDN: {e}')
            return dict(zip(('vendor', 'model', 'serial', 'firmware'), [None]*4))
    
    def get_all(self):
        """Read all implemented parameters from the instrument."""
        try:
            self.get_level()
            self.get_status()
            self.get_rate()
        except Exception as e:
            print(f"Error reading parameters: {e}")
    
    def _get_version(self):
        """Identify the device."""
        return self._execute('V')
    
    def get_level(self):
        """Get Helium level of channel 1."""
        result = self._execute('R1')
        if result:
            try:
                return float(result.replace("R", "")) / 10
            except ValueError as e:
                print(f"Error parsing level: {e}")
                return None
        return None
    
    def get_status(self):
        """Get status of the device."""
        result = self._execute('X')
        if result and len(result) > 1:
            usage = {
                0: "Channel not in use",
                1: "Channel used for Nitrogen level",
                2: "Channel used for Helium Level (Normal pulsed operation)",
                3: "Channel used for Helium Level (Continuous measurement)",
                9: "Error on channel (Usually means probe unplugged)"
            }
            try:
                return usage.get(int(result[1]), "Unknown")
            except (ValueError, IndexError) as e:
                print(f"Error parsing status: {e}")
                return "Unknown"
        return "Unknown"
    
    def get_rate(self):
        """Get helium meter channel 1 probe rate."""
        result = self._execute('X')
        if result and len(result) >= 10:
            try:
                # Status format: XabcSuuvvwwRzz
                # Channel 1 status is at positions 5-6 (uu)
                channel1_status_hex = result[5:7]
                channel1_status = int(channel1_status_hex, 16)
                
                # Check the bits according to documentation:
                # Bit 1 (0x02): Helium Probe in FAST rate
                # Bit 2 (0x04): Helium Probe in SLOW rate
                if channel1_status & 0x02:  # Bit 1 is set
                    return "FAST"
                elif channel1_status & 0x04:  # Bit 2 is set
                    return "SLOW"
                else:
                    return "UNKNOWN"
                    
            except (ValueError, IndexError) as e:
                print(f"Error parsing rate from status: {e}")
                return "Unknown"
        return "Unknown"
    
    def remote(self):
        """Set control to remote & locked."""
        self.set_remote_status(1)
    
    def local(self):
        """Set control to local & locked."""
        self.set_remote_status(0)
    
    def set_remote_status(self, mode):
        """Set remote control status."""
        status = {
            0: "Local and locked",
            1: "Remote and locked",
            2: "Local and unlocked",
            3: "Remote and unlocked",
        }
        print(f"Setting remote control status to {status.get(mode, 'Unknown')}")
        self._execute(f'C{mode}')
    
    def set_to_slow(self):
        """Set helium meter channel 1 to slow mode."""
        self.set_remote_status(1)
        print("Setting Helium Probe in SLOW rate")
        self._execute('S1')
        self.set_remote_status(3)
    
    def set_to_fast(self):
        """Set helium meter channel 1 to fast mode."""
        self.set_remote_status(1)
        print("Setting Helium Probe in FAST rate")
        self._execute('T1')
        self.set_remote_status(3)
    
    def set_rate(self, rate):
        """Set helium meter channel 1 probe rate."""
        self.set_remote_status(1)
        if rate == 0:
            self.set_to_slow()
        elif rate == 1:
            self.set_to_fast()
        else:
            print(f"Invalid rate value: {rate}. Must be 0 (SLOW) or 1 (FAST)")
            return
        self.set_remote_status(3)
        print(self.get_rate())
    
    def get_remote_status(self):
        """Get current remote control status."""
        # You'll need to implement this based on your instrument's commands
        # For now, return a default value
        return True  # Placeholder
    
    # Properties using @property decorators
    @property
    def level(self):
        """Get Helium level of channel 1."""
        return self.get_level()
    
    @property
    def status(self):
        """Get device status."""
        return self.get_status()
    
    @property
    def rate(self):
        """Get probe rate."""
        return self.get_rate()
    
    @rate.setter
    def rate(self, value):
        """Set probe rate."""
        if value == "SLOW":
            self.set_rate(0)
        elif value == "FAST":
            self.set_rate(1)
        else:
            raise ValueError("Rate must be 'SLOW' or 'FAST'")
    
    @property
    def remote_control(self):
        """Get remote control status."""
        return self.get_remote_status()
    
    @remote_control.setter
    def remote_control(self, value):
        """Set remote control status."""
        self.set_remote_status(1 if value else 0)