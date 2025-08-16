# Instrument Test GUI Generator Prompt

## Overview
Create a comprehensive Tkinter GUI that can test all properties of an instrument class. The GUI should be able to read, set, and display all properties while importing all logic from the instrument class itself.

## Requirements

### 1. Input
- **Provide:** The path to an instrument class file (e.g., `instruments/my_instrument/my_instrument.py`)

### 2. Output
Generate a complete Tkinter GUI file that:
- Automatically detects and creates controls for all properties in the instrument class
- Provides individual Read/Write buttons for each property
- Displays current property values in real-time
- Handles both read-only and read/write properties
- Includes connection management (connect/disconnect)
- Has a comprehensive log panel for all operations
- Uses a clean, organized layout with proper spacing

### 3. GUI Features

#### Connection Panel
- Resource string input field
- Connect/Disconnect buttons
- Connection status indicator

#### Status Panel
- Connection status display
- Real-time status updates

#### Properties Panel
- **Read-Only Properties:** Display value with Read button
- **Read/Write Properties:** Input field + Read/Write buttons
- Automatically generated controls for each property
- Proper labeling and organization

#### Log Panel
- Timestamped log of all operations
- Scrollable text area
- Clear operation feedback

#### Layout
- Responsive grid management
- Equal column widths
- Proper spacing and padding
- Professional appearance

### 4. Property Handling

#### Automatic Detection
- Scan instrument class for all properties
- Identify property types (string, float, int, bool)
- Determine read-only vs read/write capabilities

#### Read Operations
- Individual Read buttons for each property
- Real-time value display
- Error handling for failed reads

#### Write Operations
- Input validation for write operations
- Confirmation by reading back values
- Error handling for failed writes

#### Type Support
- **String Properties:** Text input fields
- **Numeric Properties:** Number input fields with validation
- **Boolean Properties:** Checkboxes
- **Enum Properties:** Dropdown menus

### 5. Code Structure

#### Lightweight GUI
- Minimal logic in GUI code
- Maximum delegation to instrument class
- Clean separation of concerns

#### Error Handling
- Graceful error handling
- User-friendly error messages
- Logging of all errors

#### Clean Separation
- GUI only handles UI elements and user interactions
- Instrument class handles all business logic
- No duplicate functionality

#### Reusable Pattern
- Template that can work with any instrument class
- Consistent structure and naming conventions
- Easy to modify and extend

### 6. Example Usage

The generated GUI should work as follows:

```python
# 1. User launches GUI
# 2. User enters resource string (e.g., "GPIB0::12::INSTR")
# 3. User clicks Connect
# 4. GUI automatically detects all properties from instrument class
# 5. GUI creates appropriate controls for each property
# 6. User can read individual properties with Read buttons
# 7. User can set properties with Write buttons
# 8. All operations are logged with timestamps
# 9. GUI stays synchronized with actual instrument state
```

## Expected Output

A complete, runnable Tkinter GUI file that:
- Can be saved directly to a file
- Can be executed immediately
- Requires no additional setup beyond the instrument class
- Provides comprehensive testing capabilities
- Has a professional, user-friendly interface

## Additional Considerations

### Customization Options
- Color schemes and themes
- Font sizes and styles
- Layout preferences
- Additional features (auto-refresh, data export, etc.)

### Error Scenarios
- Connection failures
- Communication timeouts
- Invalid property values
- Instrument errors

### Performance
- Responsive UI during operations
- Efficient property updates
- Memory management for long-running sessions

## Usage Instructions

1. **Provide the instrument class file path**
2. **Specify any additional requirements**
3. **Generate the GUI code**
4. **Save and run the generated file**
5. **Test all instrument properties**

This prompt will generate a GUI similar to the existing `gui_ilm210.py` but automatically adapted to work with any instrument class, making it a reusable template for testing different instruments.
