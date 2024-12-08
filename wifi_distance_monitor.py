import scapy.all as scapy
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import logging
from typing import Dict, List, Optional
import time
import threading

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
        if len(self.signal_history) > 10:  # Keep last 10 measurements
            self.signal_history.pop(0)

class WifiDistanceMonitor:
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface
        self.devices: Dict[str, WifiDevice] = {}
        self.running = False
        self.lock = threading.Lock()
        
        # RSSI calibration parameters
        self.reference_power = -50  # RSSI at 1 meter distance
        self.path_loss_exponent = 3.0  # Environment dependent
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def calculate_distance(self, rssi: float) -> float:
        """
        Calculate distance using the Log Distance Path Loss model.
        Args:
            rssi: Received Signal Strength Indicator value
        Returns:
            Estimated distance in meters
        """
        try:
            # Using the log-distance path loss model
            # distance = 10 ^ ((reference_power - RSSI) / (10 * path_loss_exponent))
            distance = 10 ** ((self.reference_power - rssi) / (10 * self.path_loss_exponent))
            return round(distance, 2)
        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return 0.0

    def packet_handler(self, packet):
        """
        Process captured WiFi packets to extract RSSI and device information.
        """
        try:
            if packet.haslayer(scapy.Dot11):
                if packet.type == 0 and packet.subtype == 8:  # Beacon frames
                    rssi = packet.dBm_AntSignal
                    mac = packet.addr2
                    ssid = packet.info.decode() if packet.info else None
                    
                    with self.lock:
                        if mac in self.devices:
                            device = self.devices[mac]
                            device.rssi = rssi
                            device.last_seen = datetime.now()
                            device.signal_history.append(rssi)
                            if len(device.signal_history) > 10:
                                device.signal_history.pop(0)
                        else:
                            self.devices[mac] = WifiDevice(
                                mac_address=mac,
                                rssi=rssi,
                                last_seen=datetime.now(),
                                ssid=ssid
                            )
                        
                        # Update distance calculation using moving average of RSSI
                        avg_rssi = np.mean(self.devices[mac].signal_history)
                        self.devices[mac].estimated_distance = self.calculate_distance(avg_rssi)
                        
        except Exception as e:
            self.logger.error(f"Error processing packet: {e}")

    def start_monitoring(self):
        """
        Start monitoring WiFi devices in a separate thread.
        """
        self.running = True
        self.logger.info(f"Starting WiFi monitoring on interface {self.interface}")
        
        def monitor():
            try:
                scapy.sniff(
                    iface=self.interface,
                    prn=self.packet_handler,
                    store=0,
                    stop_filter=lambda _: not self.running
                )
            except Exception as e:
                self.logger.error(f"Error in monitoring thread: {e}")
                self.running = False

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """
        Stop the WiFi monitoring.
        """
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        self.logger.info("WiFi monitoring stopped")

    def get_device_distances(self) -> Dict[str, float]:
        """
        Get current distances for all tracked devices.
        Returns:
            Dictionary mapping MAC addresses to distances in meters
        """
        with self.lock:
            return {
                mac: device.estimated_distance
                for mac, device in self.devices.items()
            }

    def cleanup_stale_devices(self, max_age_seconds: int = 60):
        """
        Remove devices that haven't been seen recently.
        """
        current_time = datetime.now()
        with self.lock:
            stale_macs = [
                mac for mac, device in self.devices.items()
                if (current_time - device.last_seen).total_seconds() > max_age_seconds
            ]
            for mac in stale_macs:
                del self.devices[mac]