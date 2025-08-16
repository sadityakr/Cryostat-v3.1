Here's the information about the ILM200's Serial/GPIB commands and how to interpret them, formatted for easy copy-pasting:

### **Serial/GPIB Commands**

**Monitor Commands (always recognized)**

* **Cn** \- Sets the ILM into LOCAL or REMOTE control.  
  * C0: LOCAL (Default State)  
  * C1: REMOTE & LOCKED (Front Panel Disabled)  
  * C2: LOCAL (Same as C0 for ILM)  
  * C3: REMOTE & UNLOCKED (Front Panel Active)  
* **Qn** \- Defines the communication protocol.  
  * Q0: "Normal" (Default Value)  
  * Q2: Sends \<LF\> after each \<CR\>  
  * *Note:* This command does not produce an echoed response to the computer and automatically clears the communications buffer after changing the protocol.  
* **Rnn** \- Reads a parameter. The returned value is always an integer.  
  * R1: CHANNEL 1 LEVEL  
  * R2: CHANNEL 2 LEVEL  
  * R3: CHANNEL 3 LEVEL  
  * R6: CHANNEL 1 WIRE CURRENT  
  * R7: CHANNEL 2 WIRE CURRENT  
  * R10: NEEDLE VALVE POSITION  
  * R11: CHANNEL 1 INPUT FREQUENCY/40  
  * R12: CHANNEL 2 INPUT FREQUENCY / 40  
  * R13: CHANNEL 3 INPUT FREQUENCY \* 1/40  
* **Unnnnn** \- Unlocks for "\!" and SYSTEM commands.  
  * U0: LOCKED (Power-up Default)  
  * U1: "\!" COMMAND UNLOCKED  
  * U1234: SLEEP  
  * U4321: WAKE UP  
  * U9999: "Y" COMMAND UNLOCKED  
* **V** \- Returns a message indicating the instrument type and firmware version number.  
* **Wnnnn** \- Sets a delay interval (in milliseconds) before each character is sent from ILM via the computer interface. It defaults to zero at power-up.  
* **X** \- Allows the computer to read the current ILM STATUS.

**Control Commands (recognized only in REMOTE control)**

* **Fnn** \- Sets which channel will be displayed on the channel 1 display for diagnostic purposes.  
* **Gnnn** \- Allows the needle-valve stepper motor (if fitted) to be set to a new position.  
* **Sn** \- Sets channel n to SLOW sample rate.  
* **Tn** \- Sets channel n to FAST sample rate and initiates an immediate sample pulse.

**System Commands (recognized only after correct Unnnnn command)**

* **Yn** \- Allows the contents of the RAM memory to be loaded in binary via the serial interface.  
  * If n is omitted or has the value 2, only the first 2 kilobytes of the memory are loaded.  
  * If n has the value 8, the entire 8 kilobytes are loaded.  
* **Zn** \- Allows the contents of the RAM memory to be dumped in binary via the serial interface.  
  * Omitting n or setting it to 2 results in a 2kB dump.  
  * Setting n to 8 gives a full 8 kB dump.  
* **\!n** \- Instructs the instrument that from now on, its address is to be n. (This is the ISOBUS address, not the GPIB address.)

### **Interpreting the Status Message (X Command Response)**

The response message to the "X" (Examine Status) command has the form: XabcSuuvvwwRzz

* **abc**: Three decimal digits defining Channel Usage:  
  * 0: Channel not in use  
  * 1: Channel used for Nitrogen Level  
  * 2: Channel used for Helium Level (Normal Pulsed Operation)  
  * 3: Channel used for Helium Level (Continuous Measurement)  
  * 9: Error on channel (usually means probe unplugged)  
* **uu, vv, ww**: Pairs of Hexadecimal digits defining Channel Status for each of the three channels. Each pair represents an 8-bit binary number, where the bits have the following significance (Bit 0 is LS bit):  
  * **Bit 0**: Current flowing in Helium Probe Wire (Including pre-pulse)  
  * **Bit 1**: Helium Probe in FAST rate  
  * **Bit 2**: Helium Probe in SLOW rate  
  * **Bits 3, 4**: Auto-Fill Status  
    * 00: End Fill (Level ≥ FULL)  
    * 01: Not Filling (FULL \< LEVEL ≤ FILLING)  
    * 10: Filling (FULL \< LEVEL ≤ FILLING)  
    * 11: Start Fill (LEVEL \< FILL)  
  * **Bit 5**: Low State Active (LEVEL \< LOW)  
  * **Bit 6**: Alarm Requested (As defined by CONFIG BYTE)  
  * **Bit 7**: Pre-Pulse Current Flowing  
* **zz**: A single pair of Hexadecimal digits defining Relay Status. They represent an 8-bit binary number, where the bits have the following significance (Bit 0 is LS bit):  
  * **Bit 0**: In Shut Down State  
  * **Bit 1**: Alarm Sounding (Relay 4 Active)  
  * **Bit 2**: In Alarm State (Sound may have been SILENCED)  
  * **Bit 3**: Alarm SILENCE prohibited  
  * **Bit 4**: Relay 1 Active  
  * **Bit 5**: Relay 2 Active  
  * **Bit 6**: Relay 3 Active  
  * **Bit 7**: Relay 4 Active (Duplicates bit 1\)

