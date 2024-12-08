from app.core.monitor import WifiDistanceMonitor
import time
import sys
import subprocess

def test_airport_directly():
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
