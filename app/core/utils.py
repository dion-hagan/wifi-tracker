import logging
import socket
import requests
import netifaces
import subprocess
import re
from typing import Optional, Dict, Tuple
import math

logger = logging.getLogger(__name__)

def get_device_name(ip_address: str) -> Optional[str]:
    """Try to get device hostname using reverse DNS lookup."""
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except (socket.herror, socket.gaierror):
        return None

def get_manufacturer(mac_address: str) -> Optional[str]:
    """Get device manufacturer from MAC address."""
    try:
        mac = mac_address.replace(':', '').upper()
        response = requests.get(f'https://api.maclookup.app/v2/macs/{mac}')
        if response.status_code == 200:
            data = response.json()
            return data.get('company', None)
    except Exception as e:
        logger.error(f"Error getting manufacturer: {e}")
    return None

def guess_device_type(hostname: Optional[str], manufacturer: Optional[str]) -> str:
    """Guess device type based on hostname and manufacturer."""
    if not hostname and not manufacturer:
        return "Unknown Device"

    search_text = f"{hostname} {manufacturer}".lower()
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

def detect_wifi_interface() -> str:
    """Auto-detect the WiFi interface."""
    try:
        common_interfaces = ['en0', 'en1', 'airport0']
        for interface in common_interfaces:
            if interface in netifaces.interfaces():
                try:
                    airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
                    subprocess.run(
                        [airport_path, '-I', '-i', interface],
                        check=True,
                        capture_output=True
                    )
                    logger.info(f"Detected WiFi interface: {interface}")
                    return interface
                except subprocess.CalledProcessError:
                    continue
        
        logger.warning("No WiFi interface detected, defaulting to en0")
        return 'en0'
    except Exception as e:
        logger.error(f"Error detecting WiFi interface: {e}")
        return 'en0'

def get_network_info(interface: str) -> Tuple[Optional[str], Optional[str]]:
    """Get current network IP and range."""
    try:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            netmask = addrs[netifaces.AF_INET][0]['netmask']
            cidr = sum([bin(int(x)).count('1') for x in netmask.split('.')])
            return ip, f"{ip}/{cidr}"
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
    return None, None

def get_all_device_rssi(interface: str) -> Dict[str, float]:
    """Get RSSI values for all visible devices."""
    rssi_values = {}
    try:
        airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
        
        # Scan for networks
        scan_result = subprocess.run(
            [airport_path, '-s'],
            capture_output=True,
            text=True
        )

        if scan_result.stdout:
            lines = [line.strip() for line in scan_result.stdout.split('\n') if line.strip()]
            
            if len(lines) > 1:
                for line in lines[1:]:
                    try:
                        parts = [part for part in line.split(' ') if part]
                        
                        if len(parts) >= 3:
                            mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                            if mac_match:
                                mac = mac_match.group(0).upper()
                                for part in parts:
                                    if part.startswith('-') and part[1:].isdigit():
                                        rssi = float(part)
                                        rssi_values[mac] = rssi
                                        break
                    except Exception as e:
                        logger.error(f"Error parsing line '{line}': {e}")
                        continue

    except Exception as e:
        logger.error(f"Error getting device RSSI values: {e}")
    
    return rssi_values

def calculate_distance(rssi: float, reference_power: float = -50, path_loss_exponent: float = 3.0) -> float:
    """Calculate distance using the Log Distance Path Loss model."""
    try:
        if rssi >= reference_power:
            return 0.5  # Very close, less than 1 meter
        
        distance = math.pow(10, (reference_power - rssi) / (10 * path_loss_exponent))
        return round(max(0.5, min(distance, 100)), 2)
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0
