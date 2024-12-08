# WiFi Distance Tracker

A Python-based system that monitors and estimates the distance to WiFi devices on your network using RSSI (Received Signal Strength Indicator) measurements. Features a modern web interface for real-time visualization and device management.

## Features

- Real-time monitoring of WiFi devices
- Distance estimation using RSSI and the Log Distance Path Loss model
- REST API for accessing device distance information
- Moving average calculations for stable distance estimates
- Automatic cleanup of stale device entries
- Device identification including manufacturer, type, and hostname
- Modern React-based web interface with:
  - Real-time device list with distance updates
  - Interactive device map visualization
  - Analytics dashboard
  - Configurable settings panel
- Cross-platform support (macOS and Linux)

## Requirements

- Python 3.8+
- Root/sudo privileges (required for WiFi monitoring)
- Node.js 16+ (for web interface)
- On Linux: Wireless interface in monitor mode
- On macOS: Airport utility (built-in)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wifi-tracker.git
cd wifi-tracker
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install web interface dependencies:
```bash
npm install
```

## Usage

1. Start the server (requires root privileges):
```bash
# On Linux:
sudo python3 server.py --interface wlan0 --port 5001

# On macOS:
sudo python3 server.py --interface en1 --port 5001
```

2. Start the web interface development server:
```bash
npm run dev
```

3. Access the web interface at `http://localhost:5173`

4. Or access the API directly:
```bash
curl http://localhost:5001/devices
```

The API response will be in JSON format:
```json
{
    "devices": [
        {
            "mac_address": "00:11:22:33:44:55",
            "distance": 2.5,
            "device_name": "iPhone",
            "manufacturer": "Apple Inc.",
            "device_type": "iPhone",
            "hostname": "iPhone-Device",
            "rssi": -65,
            "last_seen": "2023-12-25T12:34:56"
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

### WiFi Scanning

- On Linux: Uses wireless interface in monitor mode to capture packets
- On macOS: Uses the built-in airport utility to scan for devices
- Implements robust parsing of scan output with:
  - Header position detection for accurate column identification
  - Precise MAC address pattern matching
  - RSSI value validation
  - Comprehensive error handling

### Device Information

The system collects and processes:
- MAC addresses with manufacturer lookup
- Device type inference based on hostname and manufacturer
- Signal strength history for stable distance estimation
- Network information including IP and hostname
- Automatic device categorization (phones, laptops, IoT devices, etc.)

### Limitations

- RSSI-based distance estimation is approximate (±2-3 meters accuracy)
- Environmental factors (walls, interference) affect accuracy
- Requires root/admin privileges
- Device positions are relative to the monitoring device
- Some features may be platform-specific:
  - Linux requires monitor mode support
  - macOS uses the airport utility for scanning

## License

MIT License
