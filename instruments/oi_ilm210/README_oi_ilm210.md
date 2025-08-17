# OI ILM 210 Driver Documentation

## Properties

### Read-Only Properties
- **`level`** - Helium level reading (returns float, unit: %)
- **`status`** - Device status (returns string: "Channel not in use", "Nitrogen level", "Helium Level", etc.)

### Read/Write Properties
- **`rate`** - Probe rate (set: "SLOW" or "FAST", get: returns current rate)
- **`remote_control`** - Remote control status (set: True/False, get: returns current status)

## Methods

### Communication
- **`_execute(message)`** - Execute command with ISOBUS addressing (@n prefix)
- **`get_idn()`** - Get instrument identification (vendor, model, serial, firmware)

### Level & Status
- **`get_level()`** - Get helium level of channel 1 (returns float)
- **`get_status()`** - Get device status (returns string)
- **`get_rate()`** - Get probe rate (returns "SLOW", "FAST", or "UNKNOWN")
- **`get_all()`** - Read all parameters from instrument

### Control
- **`set_rate(rate)`** - Set probe rate (0=SLOW, 1=FAST)
- **`set_to_slow()`** - Set probe to slow mode
- **`set_to_fast()`** - Set probe to fast mode

### Remote Control
- **`remote()`** - Set control to remote & locked
- **`local()`** - Set control to local & locked
- **`set_remote_status(mode)`** - Set remote control mode (0-3)
- **`get_remote_status()`** - Get current remote control status (placeholder)

## Usage Examples

```python
# Get values
level = ilm210.level
status = ilm210.status

# Set values
ilm210.rate = "FAST"
ilm210.remote_control = True

# Control methods
ilm210.set_to_fast()
ilm210.remote()
```

## ISOBUS Addressing
All commands are automatically prefixed with `@n` where `n` is the instrument number (default: 1).
