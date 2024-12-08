from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class NetworkDevice:
    """Represents a network device with its properties and signal information."""
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
        """Initialize signal history after instance creation."""
        if self.signal_history is None:
            self.signal_history = []
        self.signal_history.append(self.rssi)
        if len(self.signal_history) > 10:
            self.signal_history.pop(0)
