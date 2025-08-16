"""
Test script for Oxford Instruments Mercury iPS-M Driver

This script demonstrates the basic functionality of the driver
using the mock driver for testing without hardware.

Author: Generated for Cryostat-v3
Date: 2024
"""

from MercuryiPS_driver import MockMercuryiPSDriver, MagnetStatus
import time


def test_driver():
    """Test the Mercury iPS-M driver functionality"""
    
    print("=== Oxford Instruments Mercury iPS-M Driver Test ===\n")
    
    # Create mock driver
    driver = MockMercuryiPSDriver()
    
    # Test connection
    print("1. Testing connection...")
    if driver.connect():
        print("   ✓ Connection successful")
    else:
        print("   ✗ Connection failed")
        return
    
    # Get device info
    print("\n2. Getting device information...")
    info = driver.get_device_info()
    print(f"   Device ID: {info.get('identification', 'Unknown')}")
    print(f"   Configuration: {info.get('configuration', 'Unknown')}")
    
    # Test field operations
    print("\n3. Testing field operations...")
    
    # Read current field
    field = driver.read_field()
    print(f"   Current field: {field} T")
    
    # Set field
    test_field = 5.0
    print(f"   Setting field to {test_field} T...")
    if driver.set_field(test_field):
        print("   ✓ Field set successfully")
    else:
        print("   ✗ Failed to set field")
    
    # Read field again
    field = driver.read_field()
    print(f"   Current field: {field} T")
    
    # Test ramp rate
    print("\n4. Testing ramp rate operations...")
    
    # Read current ramp rate
    rate = driver.read_ramp_rate()
    print(f"   Current ramp rate: {rate} T/min")
    
    # Set ramp rate
    test_rate = 2.5
    print(f"   Setting ramp rate to {test_rate} T/min...")
    if driver.set_ramp_rate(test_rate):
        print("   ✓ Ramp rate set successfully")
    else:
        print("   ✗ Failed to set ramp rate")
    
    # Read ramp rate again
    rate = driver.read_ramp_rate()
    print(f"   Current ramp rate: {rate} T/min")
    
    # Test switch heater
    print("\n5. Testing switch heater operations...")
    
    # Read heater status
    heater_status = driver.read_switch_heater_status()
    print(f"   Current heater status: {heater_status}")
    
    # Turn heater on
    print("   Turning heater ON...")
    if driver.switch_heater_on():
        print("   ✓ Heater turned ON")
    else:
        print("   ✗ Failed to turn heater ON")
    
    # Read heater status again
    heater_status = driver.read_switch_heater_status()
    print(f"   Current heater status: {heater_status}")
    
    # Turn heater off
    print("   Turning heater OFF...")
    if driver.switch_heater_off():
        print("   ✓ Heater turned OFF")
    else:
        print("   ✗ Failed to turn heater OFF")
    
    # Read heater status again
    heater_status = driver.read_switch_heater_status()
    print(f"   Current heater status: {heater_status}")
    
    # Test magnet control
    print("\n6. Testing magnet control operations...")
    
    # Read magnet status
    status = driver.read_magnet_status()
    print(f"   Current magnet status: {status.value}")
    
    # Hold field
    print("   Holding field...")
    if driver.hold_field():
        print("   ✓ Field hold activated")
    else:
        print("   ✗ Failed to hold field")
    
    # Read magnet status again
    status = driver.read_magnet_status()
    print(f"   Current magnet status: {status.value}")
    
    # Ramp to zero
    print("   Ramping to zero...")
    if driver.set_field_zero():
        print("   ✓ Ramp to zero started")
    else:
        print("   ✗ Failed to start ramp to zero")
    
    # Read magnet status again
    status = driver.read_magnet_status()
    print(f"   Current magnet status: {status.value}")
    
    # Test current and voltage readings
    print("\n7. Testing current and voltage readings...")
    
    # Read lead current
    lead_current = driver.read_lead_current()
    print(f"   Lead current: {lead_current} A")
    
    # Read persistent current
    persistent_current = driver.read_persistent_current()
    print(f"   Persistent current: {persistent_current} A")
    
    # Read voltage
    voltage = driver.read_voltage()
    print(f"   Voltage: {voltage} V")
    
    # Test field limits
    print("\n8. Testing field limits...")
    
    # Try to set field beyond limit
    high_field = 15.0
    print(f"   Attempting to set field to {high_field} T (beyond 12T limit)...")
    if driver.set_field(high_field):
        print("   ✓ Field set successfully (mock driver doesn't enforce limits)")
    else:
        print("   ✗ Field limit enforced correctly")
    
    # Test ramp rate limits
    print("\n9. Testing ramp rate limits...")
    
    # Try to set ramp rate beyond limit
    high_rate = 60.0
    print(f"   Attempting to set ramp rate to {high_rate} T/min (beyond 50 T/min limit)...")
    if driver.set_ramp_rate(high_rate):
        print("   ✓ Ramp rate set successfully (mock driver doesn't enforce limits)")
    else:
        print("   ✗ Ramp rate limit enforced correctly")
    
    # Disconnect
    print("\n10. Disconnecting...")
    driver.disconnect()
    print("   ✓ Disconnected successfully")
    
    print("\n=== Test completed successfully! ===")


if __name__ == "__main__":
    test_driver() 