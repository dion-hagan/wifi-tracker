import logging
from datetime import datetime
import subprocess
import threading
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class WifiDevice:
    mac_address: str
    rssi: float
    last_seen: datetime
    ssid: Optional[str] = None
    estimated_distance: float = 0.0
    signal_history: List[float] = None
    
    def __post_init__(self):
        if self.signal_history is None:
            self.signal_history = []
        self.signal_history.append(self.rssi)
        if len(self.signal_history) > 10:
            self.signal_history.pop(0)

class WifiDistanceMonitor:
    def __init__(self, interface: str = "en1"):
        self.interface = interface
        self.devices: Dict[str, WifiDevice] = {}
        self.running = False
        self.lock = threading.Lock()
        self.airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
        
        # RSSI calibration parameters
        self.reference_power = -50
        self.path_loss_exponent = 3.0
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Verify airport command exists
        self.verify_setup()

    def verify_setup(self):
        """Verify airport command exists and is executable."""
        try:
            self.logger.debug(f"Checking if airport command exists at: {self.airport_path}")
            result = subprocess.run([self.airport_path, "-I"], 
                                 capture_output=True, 
                                 text=True,
                                 timeout=2)
            self.logger.debug(f"Airport command test result: {result.returncode}")
        except FileNotFoundError:
            self.logger.error("Airport command not found!")
            raise
        except Exception as e:
            self.logger.error(f"Error verifying airport command: {e}")
            raise

    def calculate_distance(self, rssi: float) -> float:
        """Calculate distance using the Log Distance Path Loss model."""
        try:
            distance = 10 ** ((self.reference_power - rssi) / (10 * self.path_loss_exponent))
            return round(distance, 2)
        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return 0.0

    def run_airport_scan(self) -> Optional[str]:
        """Run airport scan command with timeout."""
        try:
            self.logger.debug("Starting airport scan...")
            result = subprocess.run(
                [self.airport_path, "-s"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.logger.debug("Airport scan completed")
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.error(f"Airport scan failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("Airport scan timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error during airport scan: {e}")
            return None

    def parse_airport_output(self, output: str) -> List[dict]:
        """Parse the output of airport -s command."""
        try:
            self.logger.debug("Starting to parse airport output")
            devices = []
            lines = output.strip().split('\n')
            
            if len(lines) <= 1:
                self.logger.warning("No networks found in scan output")
                return devices
                
            # Skip header line
            for line in lines[1:]:
                try:
                    # Split line and get RSSI (should be first number)
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        # Find RSSI (first negative number)
                        rssi = None
                        rssi_index = None
                        for i, part in enumerate(parts):
                            try:
                                value = float(part)
                                if value < 0:  # RSSI should be negative
                                    rssi = value
                                    rssi_index = i
                                    break
                            except ValueError:
                                continue
                        
                        if rssi is not None and rssi_index > 0:
                            ssid = ' '.join(parts[:rssi_index]).strip()
                            self.logger.debug(f"Found network: SSID={ssid}, RSSI={rssi}")
                            devices.append({
                                'ssid': ssid,
                                'mac': ssid.replace(' ', '_'),
                                'rssi': rssi
                            })
                except Exception as e:
                    self.logger.error(f"Error parsing line '{line}': {e}")
                    continue
            
            self.logger.debug(f"Parsed {len(devices)} devices from output")
            return devices
            
        except Exception as e:
            self.logger.error(f"Error parsing airport output: {e}")
            return []

    def scan_wifi_devices(self):
        """Scan for WiFi devices using airport utility."""
        try:
            self.logger.debug("Starting WiFi scan")
            scan_output = self.run_airport_scan()
            
            if scan_output:
                devices = self.parse_airport_output(scan_output)
                
                with self.lock:
                    self.logger.debug(f"Processing {len(devices)} devices")
                    for device in devices:
                        mac = device['mac']
                        rssi = device['rssi']
                        ssid = device['ssid']
                        
                        if mac in self.devices:
                            device_obj = self.devices[mac]
                            device_obj.rssi = rssi
                            device_obj.last_seen = datetime.now()
                            device_obj.signal_history.append(rssi)
                            if len(device_obj.signal_history) > 10:
                                device_obj.signal_history.pop(0)
                        else:
                            self.devices[mac] = WifiDevice(
                                mac_address=mac,
                                rssi=rssi,
                                last_seen=datetime.now(),
                                ssid=ssid
                            )
                        
                        avg_rssi = sum(self.devices[mac].signal_history) / len(self.devices[mac].signal_history)
                        self.devices[mac].estimated_distance = self.calculate_distance(avg_rssi)
                
                self.logger.info(f"Scan complete - found {len(devices)} networks")
            else:
                self.logger.warning("Scan produced no output")
                
        except Exception as e:
            self.logger.error(f"Error scanning WiFi devices: {e}")

    def start_monitoring(self):
        """Start monitoring WiFi devices."""
        self.running = True
        self.logger.info(f"Starting WiFi monitoring")
        
        def monitor():
            try:
                self.logger.info("Starting monitor thread")
                while self.running:
                    self.scan_wifi_devices()
                    time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error in monitor thread: {e}")
                self.running = False

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Monitor thread started")

    def stop_monitoring(self):
        """Stop WiFi monitoring."""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=3)
        self.logger.info("WiFi monitoring stopped")

    def get_device_distances(self) -> Dict[str, float]:
        """Get current distances for all tracked devices."""
        with self.lock:
            self.logger.debug(f"Getting distances for {len(self.devices)} devices")
            # Return the current state without scanning again
            return {
                f"{device.ssid}": device.estimated_distance
                for mac, device in self.devices.items()
            }