from app.core.monitor import WifiDistanceMonitor
import time
import sys
import subprocess

def test_airport_directly():
    """
    Test the macOS airport command directly to verify WiFi scanning functionality.

    This function executes the airport command with the scan option (-s) to list
    all visible WiFi networks and their properties. It's useful for debugging
    WiFi scanning issues independently of the monitor class.

    The function:
    1. Runs the airport -s command with a 5-second timeout
    2. Prints the scan results to stdout
    3. Prints any errors to stderr
    4. Handles timeout and other exceptions gracefully

    Note: Requires root privileges on macOS for full functionality.
    """
    print("Testing airport command directly...")
    try:
        result = subprocess.run(
            ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print("\nAirport scan result:")
        print(result.stdout)
        if result.stderr:
            print("\nErrors:", result.stderr)
    except subprocess.TimeoutExpired:
        print("Airport command timed out!")
    except Exception as e:
        print(f"Error running airport: {e}")

def test_scanner():
    """
    Test the WifiDistanceMonitor class functionality.

    This function performs a comprehensive test of the WiFi monitoring system:
    1. Tests the airport command directly first
    2. Creates a WifiDistanceMonitor instance
    3. Starts the monitoring thread
    4. Performs a manual device scan
    5. Retrieves and displays detailed information about discovered devices

    For each discovered device, it prints:
    - Estimated distance in meters
    - Signal strength (RSSI) in dBm
    - IP address
    - MAC address
    - Device type
    - Manufacturer (if available)
    - Hostname (if available)

    The test runs until interrupted by the user (Ctrl+C) or an error occurs.
    All exceptions are caught and logged for debugging purposes.

    Note: Requires root privileges for full functionality.
    """
    # First test airport directly
    test_airport_directly()
    
    print("\nNow testing monitor class...")
    monitor = WifiDistanceMonitor(interface="en1")
    print("Created monitor instance")
    
    try:
        print("Starting monitor...")
        monitor.start_monitoring()
        print("Monitor started")
        
        print("Doing manual scan...")
        monitor.scan_network_devices()  # Fixed method name
        print("Manual scan complete")
        
        print("\nGetting devices:")
        devices = monitor.get_device_distances()
        print(f"Found {len(devices)} devices:")
        for name, info in devices.items():  # Updated to handle the full device info
            print(f"\nDevice: {name}")
            print(f"  Distance: {info['distance']}m")
            print(f"  RSSI: {info['rssi']} dBm")
            print(f"  IP: {info['ip_address']}")
            print(f"  MAC: {info['mac_address']}")
            print(f"  Type: {info['device_type']}")
            if info['manufacturer']:
                print(f"  Manufacturer: {info['manufacturer']}")
            if info['hostname']:
                print(f"  Hostname: {info['hostname']}")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        print("\nStopping monitor...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    test_scanner()
