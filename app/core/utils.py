import logging
import socket
import requests
import netifaces
import subprocess
import re
from typing import Optional, Dict, Tuple
import math

logger = logging.getLogger(__name__)

# Common OUI prefixes for device types
OUI_PATTERNS = {
    "iPhone": [
        "A8:5C:2C", "AC:BC:32", "AC:88:FD", "24:F6:77", "F0:D1:A9", "F8:27:93",
        "04:4B:ED", "04:52:F3", "28:5A:EB", "34:08:BC", "34:C7:59", "58:B1:0F",
        "60:F4:45", "70:DE:E2", "80:B0:3D", "88:66:A5", "88:E8:7F", "90:B0:ED",
        "90:B2:1F", "90:FD:61", "9C:F3:87", "A4:B8:05", "AC:61:EA", "AC:7F:3E"
    ],
    "iPad": [
        "A4:67:06", "A4:B8:05", "AC:FD:EC", "C8:3C:85", "34:EE:16",
        "00:88:65", "04:15:52", "04:48:9A", "08:66:98", "08:6D:41", "08:E6:89",
        "0C:3E:9F", "0C:74:C2", "10:DD:B1", "14:99:E2", "18:AF:61", "1C:91:48",
        "20:A2:E4", "28:6A:BA", "2C:1F:23", "2C:BE:08", "34:C0:59", "38:B5:4D"
    ],
    "MacBook": [
        "8C:85:90", "A4:83:E7", "A8:86:DD", "F0:18:98",
        "00:3E:E1", "00:50:E4", "00:A0:40", "00:C0:CE", "04:0C:CE", "04:26:65",
        "04:48:9A", "04:52:F3", "04:54:53", "08:00:07", "0C:4D:E9", "0C:74:C2",
        "10:40:F3", "10:93:E9", "14:10:9F", "14:98:77", "18:65:90", "18:AF:61"
    ],
    "Android": [
        "40:4E:36", "44:80:EB", "70:BB:E9", "A8:9F:BA", "F8:A3:4F",
        "00:08:22", "00:18:82", "00:1A:11", "00:1C:B3", "00:21:B0", "00:24:54",
        "00:26:E8", "00:37:6D", "00:E0:91", "04:4F:4C", "04:B1:67", "08:00:1F",
        "0C:96:E6", "10:2C:6B", "10:3D:1C", "10:62:EB", "10:A5:1D", "14:A3:64"
    ],
    "Samsung": [
        "94:76:B7", "A0:82:1F", "B4:7C:9C", "CC:07:AB", "F4:42:8F",
        "00:07:AB", "00:12:47", "00:15:99", "00:17:C9", "00:1C:43", "00:21:19",
        "00:23:39", "00:24:54", "00:26:37", "00:E0:64", "04:18:0F", "08:08:C2",
        "08:37:3D", "08:D4:2B", "0C:14:20", "0C:71:5D", "0C:89:10", "10:1D:C0"
    ],
    "Google": [
        "00:1A:11", "3C:5A:B4", "54:60:09", "F4:F5:E8",
        "00:1A:11", "08:9E:08", "0C:F0:19", "10:C2:5A", "20:DF:B9", "28:BC:18",
        "2C:A1:91", "34:6A:C2", "38:8B:59", "3C:5A:B4", "48:D6:D5", "54:60:09",
        "58:6D:8F", "5C:E8:83", "60:45:BD", "64:16:66", "70:1A:04", "70:CA:9B"
    ],
    "Amazon": [
        "00:FC:8B", "34:D2:70", "40:B4:CD", "44:65:0D", "50:F5:DA", "68:37:E9", "74:C2:46",
        "0C:47:C9", "18:74:2E", "34:D2:70", "38:F7:3D", "40:B4:CD", "44:65:0D",
        "4C:EF:C0", "50:F5:DA", "68:37:E9", "6C:56:97", "74:C2:46", "78:E1:03",
        "84:D6:D0", "88:71:E5", "A0:02:DC", "AC:63:BE", "B4:7C:9C", "F0:27:2D"
    ],
    "Sonos": [
        "00:0E:58", "34:7E:5C", "48:A6:B8", "54:2A:1B", "5C:AA:FD", "78:28:CA", "94:9F:3E",
        "00:0E:58", "04:C2:9E", "08:DF:CA", "0C:43:28", "0C:49:ED", "10:02:B5",
        "10:08:C1", "14:6B:45", "1C:12:B0", "20:03:D7", "24:28:B2", "28:8F:C2",
        "2C:7E:81", "30:0E:D5", "34:7E:5C", "38:42:0B", "3C:12:AA", "40:14:7F"
    ],
    "Nest": [
        "18:B4:30", "28:BC:18", "38:8B:59", "64:16:66",
        "00:12:CA", "00:13:6C", "00:17:3F", "00:1E:06", "00:24:6C", "04:CF:8C",
        "08:3A:2F", "0C:62:A6", "10:2C:83", "10:4A:7D", "10:9A:DD", "14:58:D0",
        "18:B4:30", "1C:BA:8C", "20:3C:AE", "24:A5:2C", "28:BC:18", "2C:AA:8E"
    ],
    "Ring": [
        "00:62:6E", "2C:AA:8E", "30:91:8F", "5C:41:E6", "7C:64:56",
        "00:62:6E", "04:5C:06", "0C:47:C9", "10:9C:70", "18:B4:30", "1C:1B:68",
        "20:39:56", "24:6F:28", "28:6C:07", "2C:AA:8E", "30:91:8F", "34:3E:A4",
        "38:6B:1C", "3C:62:00", "40:01:7A", "44:21:CA", "48:6D:BB", "4C:55:CC"
    ]
}

def get_device_name(ip_address: str) -> Optional[str]:
    """
    Attempt to resolve a device's hostname using reverse DNS lookup.

    Args:
        ip_address (str): The IP address to lookup.

    Returns:
        Optional[str]: The resolved hostname if successful, None otherwise.
    """
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except (socket.herror, socket.gaierror):
        return None

def get_manufacturer(mac_address: str) -> Optional[str]:
    """
    Retrieve the manufacturer name for a given MAC address using the MacLookup API.
    Also checks against known OUI patterns for common device manufacturers.

    Args:
        mac_address (str): The MAC address to lookup (format: XX:XX:XX:XX:XX:XX).

    Returns:
        Optional[str]: The manufacturer name if found, None if the lookup fails.
    """
    try:
        # First check against known OUI patterns
        mac_prefix = mac_address[:8].upper()
        for device_type, oui_list in OUI_PATTERNS.items():
            if any(oui in mac_prefix for oui in oui_list):
                return device_type

        # If no match in OUI patterns, try API lookup
        mac = mac_address.replace(':', '').upper()
        response = requests.get(f'https://api.maclookup.app/v2/macs/{mac}')
        if response.status_code == 200:
            data = response.json()
            return data.get('company', None)
    except Exception as e:
        logger.error(f"Error getting manufacturer: {e}")
    return None

def guess_device_type(hostname: Optional[str], manufacturer: Optional[str]) -> str:
    """
    Attempt to determine the device type based on hostname and manufacturer information.
    Uses a comprehensive pattern matching system that considers both hostname and manufacturer
    information, as well as common device naming patterns.

    Args:
        hostname (Optional[str]): The device's hostname, if available.
        manufacturer (Optional[str]): The device's manufacturer, if available.

    Returns:
        str: Best guess at device type (e.g., "iPhone", "Smart TV", etc.).
    """
    if not hostname and not manufacturer:
        return "Unknown Device"

    search_text = f"{hostname} {manufacturer}".lower() if hostname else (manufacturer or "").lower()

    # Comprehensive device patterns with weighted keywords
    patterns = {
        "iPhone": ["iphone", "apple-iphone", "iphone-"],
        "iPad": ["ipad", "apple-ipad", "ipad-"],
        "MacBook": ["macbook", "mbp", "mba", "mac-book", "apple-macbook"],
        "iMac": ["imac", "apple-imac"],
        "Apple Watch": ["watch", "apple-watch"],
        "Apple TV": ["appletv", "apple-tv"],
        "Android Phone": [
            "android", "samsung", "galaxy", "pixel", "oneplus", "huawei",
            "xiaomi", "redmi", "oppo", "vivo", "realme"
        ],
        "Android Tablet": ["galaxy-tab", "nexus-tablet", "pixel-tablet"],
        "Smart TV": [
            "tv", "roku", "firetv", "fire-tv", "chromecast", "smart-tv", "samsung-tv",
            "lg-tv", "bravia", "vizio", "hisense", "television"
        ],
        "Gaming Console": [
            "playstation", "ps4", "ps5", "xbox", "nintendo", "switch",
            "xbox-one", "xbox-series", "gaming"
        ],
        "Smart Speaker": [
            "echo", "alexa", "homepod", "google-home", "nest-audio",
            "sonos", "speaker", "mini-speaker"
        ],
        "Smart Display": [
            "echo-show", "nest-hub", "portal", "smart-display",
            "home-hub", "smart-screen"
        ],
        "Security Camera": [
            "camera", "cam", "ring", "nest-cam", "arlo", "wyze",
            "security-camera", "doorbell", "surveillance"
        ],
        "Laptop": [
            "laptop", "notebook", "thinkpad", "dell", "hp", "lenovo",
            "acer", "asus", "chromebook", "surface"
        ],
        "Desktop": [
            "desktop", "pc", "computer", "workstation", "dell-pc",
            "hp-pc", "lenovo-pc"
        ],
        "Network Device": [
            "router", "switch", "access-point", "ap", "bridge",
            "gateway", "modem", "network", "wifi", "wireless"
        ],
        "Smart Home Hub": [
            "hub", "smartthings", "home-assistant", "homekit",
            "zigbee", "z-wave", "smart-hub"
        ],
        "Printer": [
            "printer", "print", "scanner", "mfp", "officejet",
            "laserjet", "epson", "canon"
        ],
        "Media Device": [
            "roku", "firetv", "apple-tv", "shield", "media-player",
            "streaming", "dvr", "tivo"
        ]
    }

    # First check if manufacturer directly matches a device type
    if manufacturer:
        for device_type, keywords in patterns.items():
            if manufacturer.lower() in device_type.lower():
                return device_type

    # Then do comprehensive pattern matching
    matched_types = []
    for device_type, keywords in patterns.items():
        for keyword in keywords:
            if keyword in search_text:
                matched_types.append(device_type)
                break

    if matched_types:
        # Return the most specific match (usually the longer name)
        return max(matched_types, key=len)

    # If no specific match found but we have a manufacturer, use it for a generic device type
    if manufacturer:
        return f"{manufacturer} Device"

    return "Unknown Device"

def detect_wifi_interface() -> str:
    """
    Auto-detect the active WiFi interface on the system.

    Attempts to find a working WiFi interface by testing common interface names
    and verifying they can be used with the airport command.

    Returns:
        str: Name of the detected WiFi interface (defaults to 'en0' if detection fails).
    """
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
    """
    Retrieve IP address and network range information for the specified interface.

    Args:
        interface (str): Name of the network interface (e.g., 'en0').

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing:
            - The interface's IP address
            - The network range in CIDR notation (e.g., '192.168.1.0/24')
            Both values will be None if the information cannot be retrieved.
    """
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
    """
    Scan for and retrieve RSSI (signal strength) values for all visible WiFi devices.

    Uses the macOS airport utility to perform a WiFi scan and extract signal strength
    information for each detected device.

    Args:
        interface (str): Name of the WiFi interface to use for scanning.

    Returns:
        Dict[str, float]: Dictionary mapping MAC addresses to their RSSI values in dBm.
    """
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
    """
    Calculate the approximate distance to a device using the Log Distance Path Loss model.

    Args:
        rssi (float): The received signal strength indicator value in dBm.
        reference_power (float, optional): Reference power at 1 meter distance. Defaults to -50.
        path_loss_exponent (float, optional): Path loss exponent for the environment.
            Defaults to 3.0 (typical for indoor environments).

    Returns:
        float: Estimated distance in meters, bounded between 0.5 and 100 meters.
    """
    try:
        if rssi >= reference_power:
            return 0.5  # Very close, less than 1 meter
        
        distance = math.pow(10, (reference_power - rssi) / (10 * path_loss_exponent))
        return round(max(0.5, min(distance, 100)), 2)
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0
