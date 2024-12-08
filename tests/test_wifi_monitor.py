import pytest
from wifi_distance_monitor import WifiDistanceMonitor, WifiDevice
from datetime import datetime
import time

@pytest.fixture
def monitor():
    monitor = WifiDistanceMonitor(interface="test0")
    yield monitor
    monitor.stop_monitoring()

def test_distance_calculation():
    monitor = WifiDistanceMonitor()
    # Test with known RSSI values
    assert monitor.calculate_distance(-50) == 1.0  # Reference power should give 1 meter
    assert monitor.calculate_distance(-60) > 1.0  # Weaker signal should give larger distance

def test_device_tracking(monitor):
    # Create a mock device
    mac = "00:11:22:33:44:55"
    rssi = -60
    device = WifiDevice(mac_address=mac, rssi=rssi, last_seen=datetime.now())
    
    # Add to monitor
    with monitor.lock:
        monitor.devices[mac] = device
    
    # Check distance calculation
    distances = monitor.get_device_distances()
    assert mac in distances
    assert distances[mac] > 0