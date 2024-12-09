import argparse
import logging

from app.core.monitor import WifiDistanceMonitor
from app import create_app

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the WiFi Distance Monitoring Server.

    This function:
    1. Parses command line arguments for WiFi interface and server port
    2. Initializes the WiFi distance monitor
    3. Performs an initial device scan
    4. Starts the background monitoring thread
    5. Launches the Flask web server

    Command Line Arguments:
        --interface: WiFi interface to use for monitoring (default: 'en1')
            Common values are 'en0' or 'en1' on macOS
        --port: Port number for the web server (default: 5001)

    The server runs until interrupted (Ctrl+C), at which point it gracefully
    shuts down the monitoring thread before exiting.

    Example Usage:
        python server.py --interface en0 --port 5000
    """
    parser = argparse.ArgumentParser(description='WiFi Distance Monitoring Server')
    parser.add_argument('--interface', default='en1', help='WiFi interface to use')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    args = parser.parse_args()

    logger.info(f"Starting server with interface {args.interface} on port {args.port}")

    try:
        # Initialize WiFi monitor
        monitor = WifiDistanceMonitor(interface=args.interface)
        
        # Do an initial scan before starting the server
        logger.info("Performing initial scan...")
        monitor.scan_network_devices()
        
        # Start the monitoring thread
        logger.info("Starting monitor thread...")
        monitor.start_monitoring()
        
        # Create and run Flask app
        logger.info("Starting Flask server...")
        app = create_app(monitor)
        app.run(host='0.0.0.0', port=args.port, threaded=True, debug=True)

    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
    finally:
        if 'monitor' in locals():
            logger.info("Stopping monitor...")
            monitor.stop_monitoring()

if __name__ == '__main__':
    main()
