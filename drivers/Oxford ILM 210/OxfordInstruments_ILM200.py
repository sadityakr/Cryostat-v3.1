# OxfordInstruments_ILM200.py class, to perform the communication between the Wrapper and the device
# Takafumi Fujita <t.fujita@tudelft.nl>, 2016
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from time import time, sleep
import logging

# Fixed import statements
try:
    import pyvisa as visa
except ImportError:
    raise ImportError("PyVISA is required. Install it with: pip install pyvisa")

try:
    from qcodes import VisaInstrument
except ImportError:
    raise ImportError("QCoDeS is required. Install it with: pip install qcodes")


class OxfordInstruments_ILM200(VisaInstrument):
    """
    This is the qcodes driver for the Oxford Instruments ILM 200 Helium Level Meter.

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_ILM200', address='<Instrument address>')
    <Instrument address> = ASRL4::INSTR

    Note: Since the ISOBUS allows for several instruments to be managed in parallel, the command
    which is sent to the device starts with '@n', where n is the ISOBUS instrument number.

    """

    def __init__(self, name, address, number=1, **kwargs):
        """
        Initializes the Oxford Instruments ILM 200 Helium Level Meter.

        Input:
            name (string)    : name of the instrument
            address (string) : instrument address
            number (int)     : ISOBUS instrument number
                                                           (number=1 is specific to the ILM in F008)

        Output:
            None
        """
        logging.debug(__name__ + ' : Initializing instrument')
        super().__init__(name, address, **kwargs)

        # Set VISA attributes with proper error handling
        try:
            self.visa_handle.set_visa_attribute(visa.constants.VI_ATTR_ASRL_STOP_BITS,
                                                visa.constants.VI_ASRL_STOP_TWO)
        except Exception as e:
            logging.warning(f"Could not set VISA attributes: {e}")

        self._address = address
        self._number = number
        self._values = {}

        self.add_parameter('level',
                           label='level',
                           get_cmd=self._do_get_level,
                           unit='%')
        self.add_parameter('status',
                           get_cmd=self._do_get_status)
        self.add_parameter('rate',
                           get_cmd=self._do_get_rate,
                           set_cmd=self._do_set_rate)

        # a dummy command to avoid the initial error
        try:
            self.get_idn()
            sleep(70e-3)  # wait for the device to be able to respond
            self._read()  # to flush the buffer
        except Exception as e:
            logging.warning(f"Initial communication failed: {e}")

    def _execute(self, message):
        """
        Write a command to the device and read answer. This function writes to
        the buffer by adding the device number at the front, instead of 'ask'.

        Input:
            message (str) : write command for the device

        Output:
            result (str) : response from device
        """
        logging.info(__name__ + ' : Send the following command to the device: %s' % message)
        try:
            self.visa_handle.write('@%s%s' % (self._number, message))
            sleep(70e-3)  # wait for the device to be able to respond
            result = self._read()
            if result.find('?') >= 0:
                logging.error("Error: Command %s not recognized" % message)
                print("Error: Command %s not recognized" % message)
                return None
            else:
                return result
        except Exception as e:
            logging.error(f"Communication error: {e}")
            return None

    def _read(self):
        """
        Reads the total bytes in the buffer and outputs as a string.

        Input:
            None

        Output:
            message (str)
        """
        try:
            # because protocol has no termination chars the read reads the number
            # of bytes in the buffer
            bytes_in_buffer = self.visa_handle.bytes_in_buffer
            if bytes_in_buffer == 0:
                return ""

            # Enhanced error handling for different PyVISA versions
            try:
                # Try newer PyVISA method
                with self.visa_handle.ignore_warning(visa.constants.VI_SUCCESS_MAX_CNT):
                    mes = self.visa_handle.visalib.read(
                        self.visa_handle.session, bytes_in_buffer)
                mes = str(mes[0].decode())
            except AttributeError:
                # Fallback for older PyVISA versions
                mes = self.visa_handle.read_raw(bytes_in_buffer).decode()

            return mes
        except Exception as e:
            logging.error(f"Read error: {e}")
            return ""

    def get_idn(self):
        r"""
        Overrides the function of Instrument since ILM does not support '\*IDN?'

        This string is supposed to be a
        comma-separated list of vendor, model, serial, and firmware, but
        semicolon and colon are also common separators so we accept them here
        as well.

        Returns:
            idn (dict): A dict containing vendor, model, serial, and firmware.
        """
        try:
            idstr = ''  # in case self.ask fails
            version_response = self._get_version()
            if version_response:
                idstr = version_response.split()
                # form is supposed to be comma-separated, but we've seen
                # other separators occasionally
                if len(idstr) >= 6:
                    idparts = [idstr[3] + ' ' + idstr[4], idstr[0], idstr[5],
                               idstr[1] + ' ' + idstr[2]]
                else:
                    idparts = [None, None, None, None]
                # in case parts at the end are missing, fill in None
                if len(idparts) < 4:
                    idparts += [None] * (4 - len(idparts))
            else:
                idparts = [None, None, None, None]
        except Exception as e:
            logging.warning('Error getting or interpreting *IDN?: ' + str(e))
            idparts = [None, None, None, None]

        return dict(zip(('vendor', 'model', 'serial', 'firmware'), idparts))

    def get_all(self):
        """
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        """
        logging.info(__name__ + ' : reading all settings from instrument')
        try:
            self.level.get()
            self.status.get()
            self.rate.get()
        except Exception as e:
            logging.error(f"Error reading parameters: {e}")

    def close(self):
        """
        Safely close connection
        """
        logging.info(__name__ + ' : Closing ILM200 connection')
        try:
            self.local()
        except Exception as e:
            logging.warning(f"Error setting to local mode: {e}")
        super().close()

    # Functions: Monitor commands
    def _get_version(self):
        """
        Identify the device

        Input:
            None

        Output:
            'ILM200 Version 1.08 (c) OXFORD 1994\r' or None if error
        """
        logging.info(__name__ + ' : Identify the device')
        return self._execute('V')

    def _do_get_level(self):
        """
        Get Helium level of channel 1.
        Input:
            None

        Output:
            result (float) : Helium level
        """
        logging.info(__name__ + ' : Read level of channel 1')
        result = self._execute('R1')
        if result:
            try:
                return float(result.replace("R", "")) / 10
            except ValueError as e:
                logging.error(f"Error parsing level: {e}")
                return None
        return None

    def _do_get_status(self):
        """
        Get status of the device.
        Input:
            None

        Output:
            status (str) : Status description
        """
        logging.info(__name__ + ' : Get status of the device.')
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
                logging.error(f"Error parsing status: {e}")
                return "Unknown"
        return "Unknown"

    def _do_get_rate(self):
        """
        Get helium meter channel 1 probe rate

        Input:
            None

        Output:
            rate (str) : Rate description
        """
        result = self._execute('X')
        print(f"DEBUG: Raw status response: {result}")  # For debugging
        if result and len(result) >= 10:
            try:
                # Status format: XabcSuuvvwwRzz
                # Channel 1 status is at positions 5-6 (uu)
                channel1_status_hex = result[5:7]  # Get the 2 hex digits for channel 1
                channel1_status = int(channel1_status_hex, 16)  # Convert hex to integer
                
                # Check the bits according to documentation:
                # Bit 1 (0x02): Helium Probe in FAST rate
                # Bit 2 (0x04): Helium Probe in SLOW rate
                if channel1_status & 0x02:  # Bit 1 is set
                    return "FAST"
                elif channel1_status & 0x04:  # Bit 2 is set
                    return "SLOW"
                else:
                    return "UNKNOWN"  # Neither bit is set
                    
            except (ValueError, IndexError) as e:
                logging.error(f"Error parsing rate from status: {e}")
                return "Unknown"
        return "Unknown"

    def remote(self):
        """
        Set control to remote & locked

        Input:
            None

        Output:
            None
        """
        logging.info(__name__ + ' : Set control to remote & locked')
        self.set_remote_status(1)

    def local(self):
        """
        Set control to local & locked

        Input:
            None

        Output:
            None
        """
        logging.info(__name__ + ' : Set control to local & locked')
        self.set_remote_status(0)

    def set_remote_status(self, mode):
        """
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        """
        status = {
            0: "Local and locked",
            1: "Remote and locked",
            2: "Local and unlocked",
            3: "Remote and unlocked",
        }
        logging.info(__name__ + ' : Setting remote control status to %s' % status.get(mode, "Unknown"))
        self._execute('C%s' % mode)

    # Functions: Control commands (only recognised when in REMOTE control)
    def set_to_slow(self):
        """
        Set helium meter channel 1 to slow mode.
        """
        self.set_remote_status(1)
        logging.info(__name__ + ' : Setting Helium Probe in SLOW rate')
        self._execute('S1')
        self.set_remote_status(3)

    def set_to_fast(self):
        """
        Set helium meter channel 1 to fast mode.
        """
        self.set_remote_status(1)
        logging.info(__name__ + ' : Setting Helium Probe in FAST rate')
        self._execute('T1')
        self.set_remote_status(3)

    def _do_set_rate(self, rate):
        """
        Set helium meter channel 1 probe rate

        Input:
            rate(int) :
            0 : "SLOW"
            1 : "FAST"
        """
        self.set_remote_status(1)
        if rate == 0:
            self.set_to_slow()
        elif rate == 1:
            self.set_to_fast()
        else:
            logging.error(f"Invalid rate value: {rate}. Must be 0 (SLOW) or 1 (FAST)")
            return
        self.set_remote_status(3)
        print(self._do_get_rate())