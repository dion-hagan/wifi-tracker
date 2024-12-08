import logging
from datetime import datetime
import subprocess
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import re
import json
import netifaces
import requests
import socket
from scapy.all import ARP, Ether, srp
import os

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class NetworkDevice:
    mac_address: str
    ip_address: str
    rssi: float
    last_seen: datetime
    device_name: Optional[str] = None
    manufacturer: Optional[str] = None
    device_type: Optional[str] = None
    hostname: Optional[str] = None
    estimated_distance: float = 0.0
    signal_history: List[float] = None
    
    def __post_init__(self):
        if self.signal_history is None:
            self.signal_history = []
        self.signal_history.append(self.rssi)
        if len(self.signal_history) > 10:
            self.signal_history.pop(0)

class WifiDistanceMonitor:
    def __init__(self, interface: str = None):
        # Auto-detect WiFi interface if none provided
        self.interface = interface or self.detect_wifi_interface()
        self.devices: Dict[str, NetworkDevice] = {}
        self.running = False
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # RSSI calibration parameters
        self.reference_power = -50
        self.path_loss_exponent = 3.0
        
        # Settings
        self.scan_interval = 2
        self.distance_threshold = 10
        
        self.verify_setup()

    def update_settings(self, scan_interval: int = None, distance_threshold: float = None):
        """Update monitor settings."""
        if scan_interval is not None:
            self.scan_interval = max(1, min(60, scan_interval))  # Clamp between 1-60 seconds
        if distance_threshold is not None:
            self.distance_threshold = max(1, min(50, distance_threshold))  # Clamp between 1-50 meters
        self.logger.info(f"Settings updated - scan_interval: {self.scan_interval}s, distance_threshold: {self.distance_threshold}m")

    def detect_wifi_interface(self) -> str:
        """Auto-detect the WiFi interface."""
        try:
            # On macOS, try common interface names
            common_interfaces = ['en0', 'en1', 'airport0']
            for interface in common_interfaces:
                if interface in netifaces.interfaces():
                    # Verify it's a WiFi interface by trying to get WiFi info
                    try:
                        airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
                        subprocess.run(
                            [airport_path, '-I', '-i', interface],
                            check=True,
                            capture_output=True
                        )
                        self.logger.info(f"Detected WiFi interface: {interface}")
                        return interface
                    except subprocess.CalledProcessError:
                        continue
            
            # If no WiFi interface found, default to en0
            self.logger.warning("No WiFi interface detected, defaulting to en0")
            return 'en0'
        except Exception as e:
            self.logger.error(f"Error detecting WiFi interface: {e}")
            return 'en0'

    def verify_setup(self):
        """Verify required commands and permissions."""
        # Check if running as root (needed for some operations)
        if os.geteuid() != 0:
            self.logger.warning("Not running as root. Some features may be limited.")
        
        # Verify airport command exists on macOS
        if os.path.exists('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'):
            self.logger.info("Found airport command")
        else:
            self.logger.warning("Airport command not found. WiFi scanning may be limited.")

    def get_device_name(self, ip_address: str) -> Optional[str]:
        """Try to get device hostname using reverse DNS lookup."""
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except (socket.herror, socket.gaierror):
            return None

    def get_manufacturer(self, mac_address: str) -> Optional[str]:
        """Get device manufacturer from MAC address."""
        try:
            # Format MAC for API: remove colons and convert to uppercase
            mac = mac_address.replace(':', '').upper()
            response = requests.get(f'https://api.maclookup.app/v2/macs/{mac}')
            if response.status_code == 200:
                data = response.json()
                return data.get('company', None)
        except Exception as e:
            self.logger.error(f"Error getting manufacturer: {e}")
        return None

    def guess_device_type(self, hostname: Optional[str], manufacturer: Optional[str]) -> str:
        """Guess device type based on hostname and manufacturer."""
        if not hostname and not manufacturer:
            return "Unknown Device"

        search_text = f"{hostname} {manufacturer}".lower()

        # Define device type patterns
        patterns = {
            "iPhone": ["iphone", "apple"],
            "iPad": ["ipad"],
            "MacBook": ["macbook", "mac book"],
            "Android Phone": ["android", "samsung", "pixel", "oneplus"],
            "Smart TV": ["tv", "roku", "firetv", "chromecast", "appletv"],
            "Gaming Console": ["playstation", "ps4", "ps5", "xbox", "nintendo"],
            "Smart Speaker": ["echo", "alexa", "homepod", "google home"],
            "Laptop": ["laptop", "notebook", "thinkpad", "dell", "hp", "lenovo"],
            "Desktop": ["desktop", "pc", "imac"],
            "Network Device": ["router", "switch", "access point", "ap"],
        }

        for device_type, keywords in patterns.items():
            if any(keyword in search_text for keyword in keywords):
                return device_type

        return "Unknown Device"

    def get_current_network_info(self) -> dict:
        """Get current WiFi network information."""
        try:
            addrs = netifaces.ifaddresses(self.interface)
            if netifaces.AF_INET in addrs:
                return addrs[netifaces.AF_INET][0]
        except Exception as e:
            self.logger.error(f"Error getting network info: {e}")
        return {}

    def get_network_range(self) -> Optional[str]:
        """Get the network range for the current network."""
        try:
            addrs = netifaces.ifaddresses(self.interface)
            if netifaces.AF_INET in addrs:
                ip = addrs[netifaces.AF_INET][0]['addr']
                netmask = addrs[netifaces.AF_INET][0]['netmask']
                # Convert to CIDR notation
                return f"{ip}/{self.netmask_to_cidr(netmask)}"
        except Exception as e:
            self.logger.error(f"Error getting network range: {e}")
        return None

    @staticmethod
    def netmask_to_cidr(netmask: str) -> int:
        """Convert netmask to CIDR notation."""
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

    def get_all_device_rssi(self) -> Dict[str, float]:
        """Get RSSI values for all visible devices."""
        rssi_values = {}
        try:
            # On macOS, use airport command to scan for all devices
            airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            if os.path.exists(airport_path):
                # First, get our current network's BSSID (router MAC)
                info_result = subprocess.run(
                    [airport_path, '-I'],
                    capture_output=True,
                    text=True
                )
                current_bssid = None
                if info_result.stdout:
                    bssid_match = re.search(r'BSSID: ([0-9a-fA-F:]{17})', info_result.stdout)
                    if bssid_match:
                        current_bssid = bssid_match.group(1).upper()

                # Then scan for all devices
                scan_result = subprocess.run(
                    [airport_path, '-s'],
                    capture_output=True,
                    text=True
                )
                
                if scan_result.stdout:
                    # Parse the airport scan output
                    lines = scan_result.stdout.strip().split('\n')
                    if len(lines) > 1:  # Ensure we have data beyond the header
                        # Parse header to find column positions
                        header = lines[0].strip()
                        rssi_pos = header.find('RSSI')
                        bssid_pos = header.find('BSSID')
                        
                        # Process each line after the header
                        for line in lines[1:]:
                            try:
                                if len(line.strip()) == 0:
                                    continue
                                    
                                # Extract RSSI (should be a negative number)
                                rssi_str = line[rssi_pos:rssi_pos+4].strip()
                                if rssi_str.startswith('-') and rssi_str[1:].isdigit():
                                    rssi = float(rssi_str)
                                    
                                    # Extract MAC address (BSSID)
                                    # Look for MAC address pattern in the line
                                    mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line[bssid_pos:])
                                    if mac_match:
                                        mac = mac_match.group(0).upper()
                                        rssi_values[mac] = rssi
                                        self.logger.debug(f"Found device - MAC: {mac}, RSSI: {rssi}")
                            except Exception as e:
                                self.logger.error(f"Error parsing line: {line}. Error: {e}")
                                continue

                # If we found our router's MAC, use its RSSI as a baseline for other devices
                if current_bssid and current_bssid in rssi_values:
                    router_rssi = rssi_values[current_bssid]
                    # Use router's RSSI as a baseline for other devices
                    for mac in rssi_values:
                        if mac != current_bssid:
                            # Adjust other devices' RSSI relative to router
                            rssi_values[mac] = router_rssi - 10  # Assume slightly weaker signal

        except Exception as e:
            self.logger.error(f"Error getting device RSSI values: {e}")
        
        return rssi_values

    def get_rssi_for_device(self, mac_address: str) -> Optional[float]:
        """Get RSSI for a specific device."""
        try:
            # Get RSSI values for all devices
            rssi_values = self.get_all_device_rssi()
            
            # Try to find the specific device's RSSI
            mac_upper = mac_address.upper()
            if mac_upper in rssi_values:
                return rssi_values[mac_upper]
            
            # If device not found in scan, use a default value
            return -75.0  # Weaker default signal

        except Exception as e:
            self.logger.error(f"Error getting RSSI for {mac_address}: {e}")
            return -75.0  # Return default value on error

    def scan_network_devices(self):
        """Scan for devices on the current network."""
        try:
            network_range = self.get_network_range()
            if not network_range:
                self.logger.error("Could not determine network range")
                return

            # Get RSSI values for all devices first
            rssi_values = self.get_all_device_rssi()

            # Use scapy for ARP scanning
            self.logger.debug(f"Scanning network range: {network_range}")
            ans, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network_range),
                timeout=2,
                verbose=False,
                iface=self.interface
            )

            # Process discovered devices
            with self.lock:
                discovered_devices = set()
                for sent, received in ans:
                    ip_address = received.psrc
                    mac_address = received.hwsrc
                    discovered_devices.add(mac_address)

                    # Get RSSI from our scan results
                    mac_upper = mac_address.upper()
                    rssi = rssi_values.get(mac_upper, -75.0)  # Use default if not found
                    
                    # Try to get hostname
                    hostname = self.get_device_name(ip_address)
                    
                    # Update existing device or create new one
                    if mac_address in self.devices:
                        device = self.devices[mac_address]
                        device.ip_address = ip_address
                        device.rssi = rssi
                        device.last_seen = datetime.now()
                        device.hostname = hostname or device.hostname
                        device.signal_history.append(rssi)
                        if len(device.signal_history) > 10:
                            device.signal_history.pop(0)
                    else:
                        # Get manufacturer info for new devices
                        manufacturer = self.get_manufacturer(mac_address)
                        device_type = self.guess_device_type(hostname, manufacturer)
                        
                        self.devices[mac_address] = NetworkDevice(
                            mac_address=mac_address,
                            ip_address=ip_address,
                            rssi=rssi,
                            last_seen=datetime.now(),
                            device_name=hostname,
                            manufacturer=manufacturer,
                            device_type=device_type
                        )
                    
                    # Update distance calculation
                    avg_rssi = sum(self.devices[mac_address].signal_history) / len(self.devices[mac_address].signal_history)
                    self.devices[mac_address].estimated_distance = self.calculate_distance(avg_rssi)

                # Log discovery results
                self.logger.info(f"Discovered {len(discovered_devices)} devices")
                
                # Remove devices not seen in the last 5 minutes
                current_time = datetime.now()
                self.devices = {
                    mac: device for mac, device in self.devices.items()
                    if (current_time - device.last_seen).total_seconds() < 300
                }

        except Exception as e:
            self.logger.error(f"Error scanning network devices: {e}")

    def calculate_distance(self, rssi: float) -> float:
        """Calculate distance using the Log Distance Path Loss model."""
        try:
            distance = 10 ** ((self.reference_power - rssi) / (10 * self.path_loss_exponent))
            return round(distance, 2)
        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return 0.0

    def start_monitoring(self):
        """Start monitoring network devices."""
        self.running = True
        self.logger.info("Starting network monitoring")
        
        def monitor():
            try:
                while self.running:
                    self.scan_network_devices()
                    time.sleep(self.scan_interval)  # Use configured scan interval
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {e}")
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
            # Filter devices based on distance threshold
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
