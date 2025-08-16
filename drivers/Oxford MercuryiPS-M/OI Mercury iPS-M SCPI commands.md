**Mercury iPS** 

7.4.10 Writing a reliable GPIB control program The GPIB interface in the iPS has been designed to be very reliable. However the GPIB control program must assume that data can be occasionally corrupted. The following sections describe features that must be built into the control program to ensure maximum reliability. 7.4.10.1 

**Timeouts** 

All commands that attempt to write or read data to an instrument must have a Timeout facility built in. This ensures that the bus only waits a specified time period for a response from an instrument. When a timeout occurs, the controller must conduct a serial poll to attempt to discover what has caused the timeout. If the serial poll also generates a timeout, the controller must reset the interface using the Interface Clear (IFC) line. If a serial poll still fails, the controller must assume that the iPS has lost power, has been disconnected, or has failed in some way. The program must then alert the operator that a fault has occurred and, if possible, continue operating the remaining instruments on the GPIB.

Here are the SCPI commands used to monitor the Oxford Instruments iPS-M SCPI power supply

1\. SCPI Protocol Conventions

* Commands are case-sensitive.   
* Keywords are a maximum of four characters long. Longer keywords will generate an invalid command response.   
* Keywords are separated by a colon (:).   
* The maximum line length is 1024 bytes (characters), including line terminators.   
* All command lines are terminated by the new line character  
   \\n (ASCII 0x0Ah). 

2\. Basic SCPI Command Structure

* \<VERB\>:\<NOUN\>:\<NOUN\>   
* All commands generate an  
   \<INVALID\> response if they cannot be interpreted. 

3\. Verbs

The interface controller can only issue two verbs:

* **READ**: A query command to read information on the specified noun.   
  * The iPS replies with a  
     STAT (status) verb followed by the requested data.   
* **SET**: Updates information for the specified noun. Attempting to set a read-only noun returns an invalid response.   
  * The iPS replies with a  
     STAT verb followed by the value that was set. 

4\. Nouns

Elements within the iPS are addressed by a hierarchical structure: 

* A Board contains a number of Devices.  
* A Device contains a number of Signals.

The structure of Nouns reflects this:

* DEV:\<UID\>:\<TYPE\>:SIG:\<TYPE\>   
* DEV:\<UID\>:\<TYPE\> \[TEMP | HTR | LVL | GAS\]   
* SIG:\<TYPE\> \[VOLT | CURR | POWR | RES | TEMP\] 

Where:

* \<UID\> is a unique identifier allocated to each board based on its SPI location.  
  * DB\#: for daughter boards, where \# is the slot id.   
  * MB\#: for the motherboard.   
* SIG is returned as a value followed by the scale.  
  * **Scale format**:   
    * n\#: nano  
    * u\#: micro  
    * m\#: milli  
    * \#: none  
    * k\#: kilo  
    * M\#: mega  
    * \# is replaced by the relevant SI units,   
    * e.g., A for Amps, V for Volts, W for Watts.

**5\. Specific SCPI Commands**

5.1. Overall Instrument Configuration

* **Command**: \*IDN?   
* **Reply Format**: IDN:OXFORD INSTRUMENTS:MERCURY dd:ss:ff   
  * dd: basic instrument type (iPS, iTC, or Cryojet)   
  * ss: serial number of the main board   
  * ff: firmware version of the instrument 

5.2. System Commands

* **Enter engineering mode**: SET:SYS:MODE:ENG:PASS:\*\*\*\*\*\* (where \*\*\*\*\*\* is the password)   
* **Exit engineering mode**: SET:SYS:MODE:NORM   
* **Change system password (in engineering mode)**:   
  * SET:SYS:MODE:ENG:PASS:\*\*\*\*\*\* (existing password)   
  * SET:SYS:PASS:newpassword (new password)   
  * SET:SYS:MODE:NORM   
* **System settings and their parameters**:   
  * SYS: system designator (N/A)  
  * TIME: time in 24 hour clock (Read/Set hh:mm:ss)  
  * DATE: date (Read/Set yyyy:mm:dd)  
  * MAN: manufacturing designator (N/A)  
  * HVER: hardware version (Read only version number)  
  * FVER: firmware version (GUI/APP) (Read only version number)  
  * SERL: unit serial number (Read only alphanumeric)  
  * MODE: mode of operation (\[NORM | ENG\]) (Read/Set enumerated value)  
  * PASS: engineering mode password (Set alphanumeric, required to enter ENG mode)   
  * FLSH: amount of free space in flash memory (Read free space in kByte)  
  * DISP: display designator (N/A)  
  * DIMA: auto dim on/off (Read/Set OFF, ON)  
  * DIMT: auto dim time (Read/Set seconds)  
  * BRIG: brightness (Read/Set 10.0 to 100.0%)  
  * RST: reset the system (Set N/A)  
  * CAT: catalogue (Read)   
* **Example of reading unit configuration**:   
  * **Command**: READ:SYS:CAT?   
  * **Example Reply (no daughter boards)**: STAT:DEV:MB0:TEMP:DEV:MB1:HTR   
  * **Example Reply (with daughter boards)**: STAT:DEV:MB0:TEMP:DEV:DB1:TEMP:DEV:MB1:HTR:DEV:DB2:HTR:DEV:DB3:AUX:DEV:DB4:LVL 

**5.3. Addressing a Magnet Controller**

To address a magnet controller, use the following structure: 

* DEV:GRPX:PSU  
* DEV:GRPY:PSU  
* DEV:GRPZ:PSU  
* **Configuration settings for a magnet controller**:   
  * PSU: Power supply designator (N/A)  
  * MAN: Manufacturing designator (N/A)  
  * HVER: Hardware version (Read only version number)  
  * FVER: Firmware version (Read only version number)  
  * SERL: Serial number (Read only alphanumeric)  
  * NICK: Nickname (Read/set alphanumeric)  
  * BIPL: Bipolar output (Read/set (EM) OFF, ON)  
  * OCNF: Output configuration (\[PARA | SERS\]) (Read/set (EM) enumerated set)  
  * CLIM: Current limit (A) (Read/set (EM) float value (0.0 to 360.00))  
  * ATOB: Current to field factor (A/T) (Read/set (EM) float value (1.00 to 30.00))  
  * IND: Magnet inductance (H) (Read/set (EM) float value (1.00 to 500.00))  
  * SWPR: Switch present (Read/set (EM) OFF, ON)  
  * SHTC: Switch heater current (mA) (Read/set (mA) float value (0.0 to 125.00))  
* **Signals for a magnet controller**:   
  * VLIM: Software voltage limit (V) (Read/set (EM) float value (0.00 to 12.49))  
  * VTRN: Ignore voltage transient (Read/set (EM) OFF, ON)  
  * VTRT: Ignore voltage transient time (s) (Read/set (EM) float value (0.00 to 120.00))  
  * VOLT: Most recent voltage reading (Read only float value)  
  * CURR: Most recent current reading (Read only float value)  
  * RCUR: Most recent current rate reading (Read only float value)  
  * FLD: Most recent field reading (Read only float value)  
  * RFLD: Most recent field rate reading (Read only float value)  
  * PCUR: Most recent persistent current reading (Read only float value)  
  * PFLD: Most recent persistent field reading (Read only float value)  
  * CSET: Most recent target current reading / current to set (Read/set float value (-CLIM to CLIM))  
  * FSET: Most recent target field reading / field to set (Read/set float value (-CLIM/ATOB to CLIM/ATOB))  
  * RCST: Most recent target current rate reading / current rate to set (Read/set float value (0.00 to 1200.00))  
  * RFST: Most recent target field rate reading / field rate to set (Read/set float value (0.00 to 50.00))  
  * SWHT: Switch heater status/set (\[ON | OFF\]) (if CURR\=PCUR) (Read/set enumerated set)  
  * SWHN: Set \[ON | OFF\] without checking if CURR\=PCUR. (Set enumerated set)  
  * ACTN: PSU action status/set (\[HOLD | RTOS | RTOZ | CLMP\]) (enumerated set)   
    * RTOS: Ramp to set  
    * RTOZ: Ramp to zero  
    * CLMP: clamp output if CURR\=0. 

5.4. Addressing a Temperature Sensor

To address a temperature sensor, use the following structure: 

* DEV:\<UID\>:TEMP  
* **Configuration settings for a temperature sensor**:   
  * TEMP: Temperature sensor designator (N/A)  
  * MAN: Manufacturing designator (N/A)  
  * HVER: Hardware version (Read only version number)  
  * FVER: Firmware version (Read only version number)  
  * SERL: Serial number (Read only alphanumeric)  
  * NICK: Nickname (Read/set alphanumeric)  
  * TYPE: (\[PTC | NTC | DDE | TCE\]) (Read/set Enumerated set)  
  * EXCT: Excitation designator (N/A)  
  * TYPE: Excitation type (\[UNIP | BIP | SOFT\]) (Read/set Enumerated set)   
  * MAG: Excitation magnitude (Read/set Float value followed by a scale)   
  * CAL: Calibration designator (N/A)  
  * FILE: Calibration file name (Read/set Filename)  
  * INT: Interpolation type (\[LIN | SPL | LAGR\]) (Read/set Enumerated set)   
  * SCAL: Scaling factor (Read/set Float value \[0.5 to 1.5\])  
  * OFFS: Offset value (Read/set Float value \[-100.0 to 100.0\])  
  * HOTL: Hot limit (Read only Float value)  
  * COLD: Cold limit (Read only Float value)  
* **Signals for a temperature sensor**:   
  * VOLT: Most recent voltage reading (Read only Float value)  
  * CURR: Most recent current reading (Read only Float value)  
  * POWR: Most recent power reading (Read only Float value)  
  * RES: Most recent resistance reading (Read only Float value)  
  * TEMP: Most recent temperature reading (Read only Float value)  
  * SLOP: Temperature sensitivity (Read only Float value)   
* **Example of configuring a temperature sensor**:   
  * **Command**: SET:DEV:MB0:TEMP:TYPE:PTC:EXCT:TYPE:UNIP:MAG:10uA:CALB:RP5:DAT   
  * **Successful Reply**: STAT:SET:DEV:MB0:TEMP:TYPE:PTC:EXCT:TYPE:UNIP:MAG:10uA:CALB:RP5:DAT   
  * **Invalid Excitation Reply**: STAT:SET:DEV:MB0:TEMP:TYPE:PTC:EXCT:TYPE:INVALID:MAG:INVALID:CALB:RP5:DAT   
* **Example of reading a temperature sensor**:   
  * **Command**: READ:DEV:MB0:SIG:VOLT?   
  * **Reply**: STAT:DEV:MB0:SIG:VOLT:12.345:mV 

**5.5. Addressing a Level Meter Sensor**

To address a level meter sensor, use the following structure: 

* DEV:\<UID\>:LVL  
* **Configuration settings for a level meter sensor**:   
  * LVL: Level sensor designator (N/A)  
  * MAN: Manufacturing designator (N/A)  
  * HVER: Hardware version (Read only version number)  
  * FVER: Firmware version (Read only version number)  
  * SERL: Serial number (Read only alphanumeric)  
  * HEL: Helium probe (N/A)  
  * RES: Resistance configuration (N/A float value)  
  * ZERO: Resistance at 0% (Ohms) (Read/set float value)  
  * FULL: Resistance at 100% (Ohms) (Read/set float value)  
  * PREP: Pre-pulse (N/A)  
  * MAG: Pre-pulse amplitude (mA) (Read/set float value)  
  * TIM: Pre-pulse duration (s) (Read/set float value)  
  * PULS: Measurement pulse (N/A)  
  * MAG: Measurement pulse amplitude (mA) (Read/set float value)  
  * TIM: Measurement pulse duration (s) (Read/set float value)   
  * DEL: Measurement pulse delay (s) (Read/set float value)  
  * NIT: Nitrogen probe (N/A)  
  * FREQ: Frequency configuration (N/A)  
  * ZERO: Frequency at 0% (Hz) (Read/set float value)  
  * FUL: Frequency at 100% (Hz) (Read/set float value)  
  * PPS: Pulse counting period in ms (Read/set float value)   
* **Signals for a level meter sensor**:   
  * HEL: Helium probe (N/A)  
  * RES: Probe measured resistance (Ohms) (Read only float value)  
  * LEV: Probe calculated level (%) (Read only float value)  
  * NIT: Nitrogen probe (N/A)  
  * COUN: Probe measured counter value (Read only unsigned integer)  
  * FREQ: Probe calculated frequency value (Hz) (Read only float value)  
  * LEV: Probe calculated level (%) (Read only float value) 

5.6. Addressing an Auxiliary I/O Daughter Board

To address an auxiliary board, use the following structure: 

* DEV:\<UID\>:AUX  
* **Configuration settings for an auxiliary board**:   
  * AUX: Auxiliary board designator (N/A)  
  * MAN: Manufacturing designator (N/A)  
  * HVER: Hardware version (Read only version number)  
  * FVER: Firmware version (Read only version number)  
  * SERL: Serial number (Read only alphanumeric)  
  * GMIN: Minimum gas flow setting (Read/set float value (0.0 to 20.0))   
  * GFSF: Gas flow scaling factor (Read/set float value (0.0 to 99.0))  
  * TES: Temperature error sensitivity (Read/set float value (0.0 to 20.0))  
  * TVES: Temperature voltage error sensitivity (Read/set float value (0.0 to 20.0))  
  * GEAR: Valve gearing (Read/set unsigned integer (0 to 7))  
  * SPD: Stepper speed (Read/set unsigned integer (0=slow, 1=fast))  
  * STEP: Present position of the stepper motor (Read only unsigned integer (0.0 to Max Steps))  
  * OPEN: Percentage open (Read/set float value (0.0 to 100.0)) 

6\. Invalid Responses

81

* \<VERB\>:INVALID: The verb cannot be interpreted.  
* \<VERB\>:\<NOUN\>:INVALID: The noun cannot be interpreted.   
* NOT\_FOUND: The UID does not exist in the system being addressed.   
* N/A: The function does not apply to the device being addressed.   
* DENIED: The user does not have permission to change the parameter being addressed. 

