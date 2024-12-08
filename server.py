from flask import Flask, jsonify, request
from flask_cors import CORS
from wifi_distance_monitor import WifiDistanceMonitor
import argparse
import logging
import threading
import time

# Custom color formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    
    # Map all possible log levels to colors
    COLORS = {
        'NOTSET': '\033[0m',     # Default
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[1;91m', # Bold Red
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        # Get the appropriate color for this level
        color = self.COLORS.get(record.levelname, self.COLORS['NOTSET'])
        reset = self.COLORS['RESET']

        # Save original values
        original_msg = record.msg
        original_levelname = record.levelname

        try:
            # Add color to the message and levelname
            record.msg = f"{color}{original_msg}{reset}"
            record.levelname = f"{color}{original_levelname}{reset}"
            
            # Format the message
            formatted_message = super().format(record)
            
            return formatted_message
        except Exception as e:
            # If any error occurs, return uncolored format
            return super().format(record)
        finally:
            # Always restore original values
            record.msg = original_msg
            record.levelname = original_levelname

# Configure root logger to capture all logs
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Create console handler with color formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
colored_formatter = ColoredFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(colored_formatter)

# Remove any existing handlers and add our colored handler
root_logger.handlers = []
root_logger.addHandler(console_handler)

# Get logger for this module
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
        monitor.scan_network_devices()
        
        # Start the monitoring thread
        logger.info("Starting monitor thread...")
        monitor.start_monitoring()
        
        # Run Flask app
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=args.port, threaded=True, debug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
    finally:
        if monitor:
            logger.info("Stopping monitor...")
            monitor.stop_monitoring()

if __name__ == '__main__':
    main()
