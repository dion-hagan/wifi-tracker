from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class NetworkDevice:
    """Represents a network device with its properties and signal information.

    This class stores comprehensive information about a network device including its
    identification, signal strength, and historical data. It's used to track and
    monitor devices over time.

    Attributes:
        mac_address (str): The device's MAC address for unique identification
        ip_address (str): The device's IP address on the network
        rssi (float): Current Received Signal Strength Indicator value in dBm
        last_seen (datetime): Timestamp of the most recent device detection
        device_name (Optional[str]): Human-readable name of the device, if available
        manufacturer (Optional[str]): Device manufacturer name, if identifiable
        device_type (Optional[str]): Type/category of the device, if known
        hostname (Optional[str]): Network hostname of the device, if available
        estimated_distance (float): Calculated distance based on signal strength in meters
        signal_history (List[float]): Historical RSSI values, limited to last 10 readings
    """
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
        """Initialize and maintain the signal history after instance creation.

        This method ensures the signal_history is properly initialized and maintains
        a rolling window of the 10 most recent RSSI values. When a new instance is
        created, it automatically adds the initial RSSI value to the history and
        removes the oldest value if the history exceeds 10 entries.
        """
        if self.signal_history is None:
            self.signal_history = []
        self.signal_history.append(self.rssi)
        if len(self.signal_history) > 10:
            self.signal_history.pop(0)
