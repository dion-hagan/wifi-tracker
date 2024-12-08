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
        
        self.verify_setup()

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

    def get_rssi_for_device(self, mac_address: str) -> Optional[float]:
        """Get RSSI for a specific device."""
        try:
            # On macOS, use airport command
            airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            if os.path.exists(airport_path):
                result = subprocess.run(
                    [airport_path, '-I', '-i', self.interface],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    # Try to find RSSI for the specific device
                    rssi_match = re.search(r'agrCtlRSSI:\s*(-\d+)', result.stdout)
                    if rssi_match:
                        return float(rssi_match.group(1))
                    
                    # If specific device RSSI not found, use overall RSSI
                    noise_match = re.search(r'agrCtlNoise:\s*(-\d+)', result.stdout)
                    if noise_match:
                        noise = float(noise_match.group(1))
                        # Estimate RSSI based on noise floor
                        return noise + 30  # Typical signal-to-noise ratio

        except Exception as e:
            self.logger.error(f"Error getting RSSI for {mac_address}: {e}")
        
        # Return a default value if we couldn't get actual RSSI
        return -70.0

    def scan_network_devices(self):
        """Scan for devices on the current network."""
        try:
            network_range = self.get_network_range()
            if not network_range:
                self.logger.error("Could not determine network range")
                return

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

                    # Get RSSI
                    rssi = self.get_rssi_for_device(mac_address)
                    
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
                    time.sleep(2)
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
            }
