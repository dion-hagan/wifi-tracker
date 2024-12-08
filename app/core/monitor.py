import logging
import threading
import time
from datetime import datetime
from typing import Dict
import os
from scapy.all import ARP, Ether, srp

from app.core.models import NetworkDevice
from app.core.utils import (
    detect_wifi_interface,
    get_device_name,
    get_manufacturer,
    guess_device_type,
    get_network_info,
    get_all_device_rssi,
    calculate_distance
)

logger = logging.getLogger(__name__)

class WifiDistanceMonitor:
    """Monitors WiFi devices and their distances."""
    
    def __init__(self, interface: str = None):
        # Auto-detect WiFi interface if none provided
        self.interface = interface or detect_wifi_interface()
        self.devices: Dict[str, NetworkDevice] = {}
        self.running = False
        self.lock = threading.Lock()
        
        # RSSI calibration parameters
        self.reference_power = -50  # Typical value at 1 meter distance
        self.path_loss_exponent = 3.0  # Typical value for indoor environments
        
        # Settings
        self.scan_interval = 2
        self.distance_threshold = 30
        
        self.verify_setup()

    def update_settings(self, scan_interval: int = None, distance_threshold: float = None):
        """Update monitor settings."""
        if scan_interval is not None:
            self.scan_interval = max(1, min(60, scan_interval))
        if distance_threshold is not None:
            self.distance_threshold = max(1, min(100, distance_threshold))
        logger.info(f"Settings updated - scan_interval: {self.scan_interval}s, distance_threshold: {self.distance_threshold}m")

    def verify_setup(self):
        """Verify required commands and permissions."""
        if os.geteuid() != 0:
            logger.warning("Not running as root. Some features may be limited.")
        
        airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
        if os.path.exists(airport_path):
            logger.info("Found airport command")
        else:
            logger.warning("Airport command not found. WiFi scanning may be limited.")

    def scan_network_devices(self):
        """Scan for devices on the current network."""
        try:
            # Get RSSI values for all devices first
            rssi_values = get_all_device_rssi(self.interface)

            # Add WiFi devices first
            with self.lock:
                for mac_address, rssi in rssi_values.items():
                    if mac_address not in self.devices:
                        self.devices[mac_address] = NetworkDevice(
                            mac_address=mac_address,
                            ip_address="",  # Will be updated if found via ARP
                            rssi=rssi,
                            last_seen=datetime.now(),
                            device_name=None,
                            manufacturer=get_manufacturer(mac_address),
                            device_type="WiFi Device"
                        )
                    else:
                        self.devices[mac_address].rssi = rssi
                        self.devices[mac_address].last_seen = datetime.now()
                        self.devices[mac_address].signal_history.append(rssi)
                        if len(self.devices[mac_address].signal_history) > 10:
                            self.devices[mac_address].signal_history.pop(0)

            # Try ARP scanning to get IP addresses
            _, network_range = get_network_info(self.interface)
            if network_range:
                logger.debug(f"Scanning network range: {network_range}")
                ans, _ = srp(
                    Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_range),
                    timeout=2,
                    verbose=False,
                    iface=self.interface
                )

                # Update devices with IP addresses from ARP scan
                with self.lock:
                    discovered_devices = set()
                    for sent, received in ans:
                        ip_address = received.psrc
                        mac_address = received.hwsrc.upper()
                        discovered_devices.add(mac_address)

                        if mac_address in self.devices:
                            device = self.devices[mac_address]
                            device.ip_address = ip_address
                            hostname = get_device_name(ip_address)
                            device.hostname = hostname or device.hostname
                            if not device.manufacturer:
                                device.manufacturer = get_manufacturer(mac_address)
                            device.device_type = guess_device_type(hostname, device.manufacturer)
                        else:
                            # Device found via ARP but not WiFi
                            self.devices[mac_address] = NetworkDevice(
                                mac_address=mac_address,
                                ip_address=ip_address,
                                rssi=-100,  # Default weak signal
                                last_seen=datetime.now(),
                                hostname=get_device_name(ip_address),
                                manufacturer=get_manufacturer(mac_address),
                                device_type="Network Device"
                            )

                    logger.info(f"Discovered {len(discovered_devices)} devices")

                # Update distance calculations
                for mac_address, device in self.devices.items():
                    avg_rssi = sum(device.signal_history) / len(device.signal_history)
                    device.estimated_distance = calculate_distance(
                        avg_rssi,
                        self.reference_power,
                        self.path_loss_exponent
                    )

                # Remove old devices
                current_time = datetime.now()
                self.devices = {
                    mac: device for mac, device in self.devices.items()
                    if (current_time - device.last_seen).total_seconds() < 300
                }

        except Exception as e:
            logger.error(f"Error scanning network devices: {e}")

    def start_monitoring(self):
        """Start monitoring network devices."""
        self.running = True
        logger.info("Starting network monitoring")
        
        def monitor():
            try:
                while self.running:
                    self.scan_network_devices()
                    time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                self.running = False

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop network monitoring."""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=3)

    def get_device_distances(self) -> Dict[str, dict]:
        """Get current distances and info for all tracked devices."""
        with self.lock:
            return {
                device.device_name if device.device_name else f"Device ({device.mac_address})": {
                    "distance": device.estimated_distance,
                    "rssi": device.rssi,
                    "last_seen": device.last_seen.isoformat(),
                    "ip_address": device.ip_address,
                    "mac_address": device.mac_address,
                    "manufacturer": device.manufacturer,
                    "device_type": device.device_type,
                    "hostname": device.hostname
                }
                for device in self.devices.values()
                if device.estimated_distance <= self.distance_threshold
            }
