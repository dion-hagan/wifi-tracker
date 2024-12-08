from flask import Flask, jsonify, request
from flask_cors import CORS
from wifi_distance_monitor import WifiDistanceMonitor
import argparse
import logging
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
monitor = None

# Default settings
settings = {
    "scan_interval": 2,
    "distance_threshold": 10
}

@app.route('/devices', methods=['GET'])
def get_devices():
    """API endpoint to get all detected devices and their distances"""
    logger.debug("Received request for /devices")
    
    if not monitor:
        logger.error("Monitor not initialized")
        return jsonify({"error": "Monitor not initialized"}), 500
    
    try:
        logger.debug("Getting device distances from monitor...")
        devices = monitor.get_device_distances()
        logger.debug(f"Got devices: {devices}")
        
        # Return immediately
        return jsonify({"devices": devices})
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    """API endpoint to get or update settings"""
    global settings
    
    if request.method == 'GET':
        return jsonify(settings)
    
    elif request.method == 'POST':
        try:
            new_settings = request.get_json()
            # Validate settings
            if not isinstance(new_settings.get('scan_interval'), (int, float)) or \
               not isinstance(new_settings.get('distance_threshold'), (int, float)):
                return jsonify({"error": "Invalid settings format"}), 400
            
            # Update settings
            settings.update(new_settings)
            
            # Update monitor settings if it exists
            if monitor:
                monitor.update_settings(
                    scan_interval=settings['scan_interval'],
                    distance_threshold=settings['distance_threshold']
                )
            
            return jsonify({"message": "Settings updated successfully"})
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

def main():
    parser = argparse.ArgumentParser(description='WiFi Distance Monitoring Server')
    parser.add_argument('--interface', default='en1', help='WiFi interface to use')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()

    logger.info(f"Starting server with interface {args.interface} on port {args.port}")

    try:
        global monitor
        monitor = WifiDistanceMonitor(interface=args.interface)
        
        # Do an initial scan before starting the server
        logger.info("Performing initial scan...")
        monitor.scan_network_devices()  # Fixed method name
        
        # Start the monitoring thread
        logger.info("Starting monitor thread...")
        monitor.start_monitoring()
        
        # Run Flask app
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=args.port, threaded=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
    finally:
        if monitor:
            logger.info("Stopping monitor...")
            monitor.stop_monitoring()

if __name__ == '__main__':
    main()