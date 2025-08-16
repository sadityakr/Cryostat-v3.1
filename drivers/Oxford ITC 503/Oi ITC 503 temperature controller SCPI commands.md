Here's the extracted information regarding serial/GPIB commands and how to interpret their output strings for the ITC503, cleaned for a markdown file without references:

The ITC503 can be remotely operated via its RS232 (Serial) or GPIB (IEEE-488) interfaces. Both interfaces use the same command protocols.

**Communication Protocols:**

* All commands are strings of printing ASCII characters, terminated by a Carriage Return (\<CR\>). An optional Line Feed (\<LF\>) character after the \<CR\> is ignored.  
* Unless a command starts with a $ (dollar) character, ITC503 will send a response.  
* Responses are strings of one or more printing ASCII characters, terminated by a \<CR\>, optionally followed by an \<LF\>.  
* Responses are normally sent immediately, but may be delayed if a front panel button is pressed when the command is received.  
* If a command starts with $ , no response will be sent. This is typically used for commands sent to all instruments simultaneously on an ISOBUS to prevent conflicts.  
* If a command is not recognized, has an illegal parameter, or cannot be obeyed, an error response ? followed by all or part of the command string will be sent.  
* The most common reason for a command error is attempting a control command while ITC503 is in LOCAL control.  
* The W command can be used to instruct ITC503 to send data more slowly for slow computers.  
* Numeric parameters are treated as signed decimal numbers with an appropriately placed decimal point, mimicking the front panel display.

**ISOBUS Protocol (for RS232):**

* Allows multiple instruments to be driven from a single RS232 port.  
* Each instrument has a unique address (0 to 9\) in non-volatile memory (default for ITC503 is 1).  
* Commands for ISOBUS operation must start with a special ISOBUS control character:  
  * @n: Addresses the command to instrument n. This instrument obeys and returns its usual response; others ignore.  
  * $: Instructs all instruments to send no reply. Use with caution as it suppresses error responses.  
  * &: Instructs the instrument to ignore subsequent ISOBUS control characters.  
  * \!n: Sets the instrument's ISOBUS address to n. This command should only be used when one instrument is powered up and connected to ISOBUS, and only after a U command with a non-zero password.

**GPIB (IEEE-488) Interface:**

* Connections via a standard 24-way GPIB connector, conforming to IEEE-488.1.  
* GPIB connections should not be made or broken while instruments are powered up to avoid damage.  
* Complies fully with IEEE-488.1-1987 as a talker/listener.  
* Supports generation of service requests and responds to serial poll and device clear commands. Does not support parallel polling or trigger functions.  
* GPIB address is unique (default 24). Can be changed via Test Mode.  
* Q2 command: After power-up, sending Q2 will cause subsequent messages to be terminated by \<CRLF\> instead of just \<CR\>.  
* The interface never asserts the EOI line at the end of a message.  
* **Status Byte (Serial Poll):** Three bits are significant:  
  * Bit 6 (Value 64 decimal): RQS (Requesting Service)  
  * Bit 4 (Value 16 decimal): MAV (Message Available)  
  * Bit 1 (Value 2 decimal): BAV (Byte Available)  
  * BAV is set when at least one byte is available. MAV is set when a complete message (including \<CR\> or \<LF\>) is available.  
  * RQS is set when the interface asserts the GPIB SRQ line. Reading the status byte clears the RQS bit and releases the SRQ line.  
  * Status byte is updated every millisecond.  
* **Service Request Line (SRQ):** Issued when a complete message is available to be read, unless already addressed to TALK.  
* **Device Clear Function:** Clears communication buffers, but does not reset temperature control functions. Can be sent via GPIB DCL or SDC messages.  
* **Interface Clear (IFC) Function:** Clears GPIB interface functions but does not clear pending data in buffers or affect temperature control.  
* **Non-Implemented Features:** Does not use GPIB Remote Enable (REN) for LOCAL/REMOTE switching (uses C command), nor does it respond to GPIB LOCAL LOCKOUT or GOTO LOCAL commands. Does not respond to Parallel Poll.  
* **GPIB to ISOBUS Gateway:** An ITC503 with GPIB can act as a GATEWAY. All characters received via GPIB are echoed to RS232, and vice versa. Allows other Oxford Instruments products without GPIB to be controlled via GPIB using ISOBUS cables and protocols. The GPIB GATEWAY MASTER has ISOBUS address @0.

**Command Categories:**

* **MONITOR COMMANDS:** Always recognized.  
* **CONTROL COMMANDS:** Recognized only in REMOTE control.  
* **SYSTEM COMMANDS:** Recognized only after the correct "UNLOCK KEY".  
* **SPECIALIST COMMANDS:** Primarily for engineering use and high-level system software.

**Command List & Syntax:**

* **Cn COMMAND:** Sets ITC503 into LOCAL or REMOTE control and locks/unlocks the front panel.  
  * C0: LOCAL & LOCKED (Default State)  
  * C1: REMOTE & LOCKED (Front Panel Disabled)  
  * C2: LOCAL & UNLOCKED  
  * C3: REMOTE & UNLOCKED (Front Panel Active for display, not adjustment)  
  * **Response:** If accepted, echoes the command letter.  
* **Qn COMMAND:** Defines the communication protocol.  
  * Q0: "Normal" (Default Value)  
  * Q2: Sends \<LF\> after each \<CR\>.  
  * **Response:** Does not produce an echoed response.  
* **Rn COMMAND:** Reads parameters. Returned value is an integer.  
  * R0: SET TEMPERATURE  
  * R1: SENSOR 1 TEMPERATURE  
  * R2: SENSOR 2 TEMPERATURE  
  * R3: SENSOR 3 TEMPERATURE  
  * R4: TEMPERATURE ERROR (+ve when SET \> MEASURED)  
  * R5: HEATER O/P (as % of current limit)  
  * R6: HEATER O/P (as Volts, approx.)  
  * R7: GAS FLOW O/P (arbitrary units)  
  * R8: PROPORTIONAL BAND  
  * R9: INTEGRAL ACTION TIME  
  * R10: DERIVATIVE ACTION TIME  
  * R11: CHANNEL 1 FREQ/4 (Service diagnostic)  
  * R12: CHANNEL 2 FREQ/4 (Service diagnostic)  
  * R13: CHANNEL 3 FREQ/4 (Service diagnostic)  
  * **Response:** Command letter followed by the requested value (e.g., R1.234).  
* **Unnnnn COMMAND:** UNLOCK command to access SYSTEM commands. nnnnn is the key parameter.  
  * U0: LOCKED (Power-up Default)  
  * U1: \! COMMAND UNLOCKED  
  * U1234: SLEEP (for GATEWAY MASTER, ignores GPIB data)  
  * U4321: WAKE UP (for GATEWAY MASTER)  
  * U9999: L, Y, & Z COMMANDS UNLOCKED.  
  * **Response:** If accepted, echoes the command letter.  
* **V COMMAND:** Returns the instrument type and firmware version number. No parameters.  
  * **Response:** Message indicating type and version (e.g., VITC503 1.07).  
* **Wnnnn COMMAND:** Sets a delay interval (nnnn in milliseconds) before each character is sent from ITC503. Defaults to zero at power-up.  
  * **Response:** If accepted, echoes the command letter.  
* **X COMMAND:** Reads the current ITC503 STATUS. No parameters.  
  * **Response:** Message string in the form XnAnCnSnnHnLn.  
    * Xn: SYSTEM STATUS (always zero currently)  
    * An: AUTO/MAN STATUS (n as for A COMMAND, \+4 during initial AutoGFS calibration)  
    * Cn: LOC/REM/LOCK STATUS (n as for C COMMAND)  
    * Snn: SWEEP STATUS (nn=0-32)  
      * nn=0: SWEEP NOT RUNNING  
      * nn=2P-1: SWEEPING to step P  
      * nn=2P: HOLDING at step P  
    * Hn: CONTROL SENSOR (n as for H COMMAND)  
    * Ln: AUTO-PID STATUS (n as for L COMMAND)  
* **An COMMAND:** Sets heater and gas flow control to AUTO or MANUAL.  
  * A0: HEATER MANUAL, GAS MANUAL  
  * A1: HEATER AUTO, GAS MANUAL  
  * A2: HEATER MANUAL, GAS AUTO  
  * A3: HEATER AUTO, GAS AUTO  
  * **Response:** If accepted, echoes the command letter.  
* **Pnnnn, Innnn, Dnnnn COMMANDS:** Set PROPORTIONAL, INTEGRAL, and DERIVATIVE control terms.  
  * Values for nnnn correspond to section 6.7.  
  * **Response:** If accepted, echoes the command letter.  
* **Fnn COMMAND:** Sets the front panel display to show an internal parameter.  
  * nn can take the same values as for the R command.  
  * **Response:** If accepted, echoes the command letter.  
* **Gnnn COMMAND:** Sets the GAS FLOW to a defined value (nnn as percentage to 0.1% resolution). For use with AutoGFS.  
  * **Response:** If accepted, echoes the command letter.  
* **Hn COMMAND:** Defines the sensor to be used for automatic control.  
  * n can be 1-3.  
  * **Response:** If accepted, echoes the command letter.  
* **Ln COMMAND:** Enables or disables use of Auto-PID values.  
  * L0: DISABLES USE OF AUTO-PID  
  * L1: USES AUTO-PID  
  * **Response:** If accepted, echoes the command letter.  
* **Mnnn COMMAND:** Sets the maximum heater voltage ITC503 may deliver. nnn is approximate in 0.1 volt resolution. M0 specifies a dynamically varying limit.  
  * **Response:** If accepted, echoes the command letter.  
* **Onnn COMMAND:** Sets the required heater output in MANUAL. The parameter nnn is expressed as a percentage (0 to 99.9) of the maximum heater voltage set by the M command.  
  * **Response:** If accepted, echoes the command letter.  
* **Sn COMMAND:** Starts and stops a sweep remotely.  
  * S0: STOPS SWEEP  
  * S1: STARTS SWEEP  
  * n from 2-32: Enters sweep program part way through. n has same significance as S in status message.  
  * **Response:** If accepted, echoes the command letter.  
* **Tnnnnn COMMAND:** Sets a set point temperature. nnnnn is the required temperature as a signed decimal number.  
  * **Response:** If accepted, echoes the command letter.  
* **Yn COMMAND:** Loads RAM memory contents in binary via the serial interface. Not a user command.  
  * n omitted or n=2: loads first 2 kilobytes.  
  * n=8: loads entire 8 kilobytes.  
  * **Response:** If accepted, echoes the command letter.  
* **Zn COMMAND:** Dumps RAM memory contents in binary via the serial interface. Not a user command.  
  * n omitted or n=2: dumps 2 kilobytes.  
  * n=8: dumps full 8 kilobytes.  
  * **Response:** If accepted, echoes the command letter.  
* **\~ COMMAND:** Stores RAM memory contents to EEPROM. Not a user command. (Firmware v1.07 and later).  
  * **Response:** If accepted, the display will show "Stor" and a response will be sent when complete. Otherwise, ?- error.

**Specialist Commands (all lower-case letters):** Not generally for customer use.

* **xnnn & ynnn COMMANDS:** Set pointers into tables for loading/examining data. nnn are decimal integers 0 to 128\.  
  * **Response:** If accepted, echoes the command letter.  
* **snnnnn COMMAND:** Programs individual steps of the sweep table. Requires x pointer set to sweep step (1-16), y pointer selects parameter:  
  * y=1: Set Point Temperature  
  * y=2: Sweep Time to Set Point  
  * y=3: Hold Time at Set Point  
  * **Response:** If accepted, echoes the command letter.  
* **r COMMAND:** Reads individual steps of the sweep table using x and y pointers.  
  * **Response:** Returns the value from the selected sweep table entry.  
* **w COMMAND:** Wipes all values entered by the s command (or manually).  
  * **Response:** If accepted, echoes the command letter.  
* **pnnnnn COMMAND:** Programs Auto-PID settings for Auto-PID mode. x pointer defines entry (1-32), y pointer selects parameter:  
  * y=1: Upper Temperature Limit  
  * y=2: Proportional Band  
  * y=3: Integral Action Time  
  * Y=4: Derivative Action Time  
  * **Response:** If accepted, echoes the command letter.  
* **q COMMAND:** Reads individual entries in the Auto-PID table using x and y pointers.  
  * **Response:** Returns the value from the selected Auto-PID table entry.  
* **vann COMMAND:** Programs values into the custom target heater voltage table. x pointer defines the element (1-64), y pointer is not used.  
  * **Response:** If accepted, echoes the command letter.  
* **t COMMAND:** Reads back the value from the x pointer in the custom target heater voltage table.  
  * **Response:** Returns the value.  
* **cnnn COMMAND:** Sets the values of the Gas Flow Configuration parameters. x pointer defines which parameter is set.  
  * **Response:** If accepted, echoes the command letter.  
* **d COMMAND:** Reads Gas Flow Configuration Parameters. x pointer determines which parameter is read.  
  * **Response:** Returns the parameter value.  
* **m COMMAND:** Returns the status of the flow control algorithm (integer 0-255). Valid only when GAS is in AUTO.  
  * **Response:** Returns an integer. Bits significance:  
    * BIT 7, 6, 5: Not Used  
    * BIT 4: Heater Error Sign (1=−ve)  
    * BIT 3: Temperature Error Sign  
    * BIT 2: Slow Valve Action Occurring  
    * BIT 1: Cooldown Termination Occurring  
    * BIT 0: Fast Cooldown Occurring  
* **n COMMAND:** Reads the current heater target voltage. Valid only if in GAS AUTO.  
  * **Response:** Returns value to one decimal place.  
* **o COMMAND:** Reads Valve Scaling (diagnostic value). Valid only in GAS AUTO.  
  * **Response:** Returns the value.

