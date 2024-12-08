# WiFi Distance Tracker

A Python-based system that monitors and estimates the distance to WiFi devices on your network using RSSI (Received Signal Strength Indicator) measurements.

## Features

- Real-time monitoring of WiFi devices
- Distance estimation using RSSI and the Log Distance Path Loss model
- REST API for accessing device distance information
- Moving average calculations for stable distance estimates
- Automatic cleanup of stale device entries

## Requirements

- Python 3.8+
- Root/sudo privileges (required for WiFi monitoring)
- Linux-based system with wireless interface in monitor mode

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wifi-tracker.git
cd wifi-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server (requires root privileges):
```bash
sudo python3 server.py --interface wlan0 --port 5000
```

2. Access the API:
```bash
curl http://localhost:5000/devices
```

The response will be in JSON format:
```json
{
    "devices": [
        {
            "mac_address": "00:11:22:33:44:55",
            "distance": 2.5
        }
    ]
}
```

## Testing

Run the tests using pytest:
```bash
pytest tests/
```

## Technical Details

### Distance Calculation

The system uses the Log Distance Path Loss model to estimate distances:
```
distance = 10 ^ ((reference_power - RSSI) / (10 * path_loss_exponent))
```

Where:
- reference_power: RSSI at 1 meter distance (default: -50 dBm)
- path_loss_exponent: Environment-dependent value (default: 3.0)

### Limitations

- RSSI-based distance estimation is approximate (±2-3 meters accuracy)
- Environmental factors (walls, interference) affect accuracy
- Requires root/admin privileges
- Device positions are relative to the monitoring device

## License

MIT License