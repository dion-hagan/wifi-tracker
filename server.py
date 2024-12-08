from flask import Flask, jsonify
from flask_cors import CORS
from wifi_distance_monitor import WifiDistanceMonitor
import argparse

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
monitor = None

@app.route('/devices', methods=['GET'])
def get_devices():
    """
    API endpoint to get all detected devices and their distances
    """
    if not monitor:
        return jsonify({"error": "Monitor not initialized"}), 500
    
    devices = monitor.get_device_distances()
    return jsonify({"devices": [
        {
            "mac_address": mac,
            "distance": distance,
        } for mac, distance in devices.items()
    ]})

def main():
    parser = argparse.ArgumentParser(description='WiFi Distance Monitoring Server')
    parser.add_argument('--interface', default='wlan0', help='WiFi interface to use')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()

    global monitor
    monitor = WifiDistanceMonitor(interface=args.interface)
    monitor.start_monitoring()
    
    try:
        app.run(host='0.0.0.0', port=args.port)
    finally:
        monitor.stop_monitoring()

if __name__ == '__main__':
    main()
