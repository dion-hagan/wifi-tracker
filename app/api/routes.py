from flask import Blueprint, jsonify, request
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# Global monitor instance to be set by the main application
monitor = None

def init_routes(wifi_monitor):
    """
    Initialize API routes with a WiFi monitor instance.

    Args:
        wifi_monitor: The WifiDistanceMonitor instance to use for device tracking.
    """
    global monitor
    monitor = wifi_monitor

@api.route('/devices', methods=['GET'])
def get_devices():
    """
    API endpoint to retrieve all detected devices and their distances.

    Returns:
        flask.Response: JSON response containing:
            On success: {"devices": {
                "device_name": {
                    "distance": float,
                    "rssi": float,
                    "last_seen": str (ISO format),
                    "ip_address": str,
                    "mac_address": str,
                    "manufacturer": str,
                    "device_type": str,
                    "hostname": str
                }
            }}
            On error: {"error": str}, status code 500
    """
    logger.debug("Received request for /devices")
    
    if not monitor:
        logger.error("Monitor not initialized")
        return jsonify({"error": "Monitor not initialized"}), 500
    
    try:
        logger.debug("Getting device distances from monitor...")
        devices = monitor.get_device_distances()
        logger.debug(f"Got devices: {devices}")
        return jsonify({"devices": devices})
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@api.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    """
    API endpoint to get or update application settings.

    Methods:
        GET: Retrieve current settings
        POST: Update settings with new values in request body

    Returns:
        flask.Response: JSON response containing:
            GET: Current settings object with all configuration values
            POST success: {
                "message": "Settings updated successfully",
                "settings": {updated settings object}
            }
            POST error: {"error": str}, status code 500
    """
    if request.method == 'GET':
        return jsonify(settings.get_all())
    
    elif request.method == 'POST':
        try:
            new_settings = request.get_json()
            updated_settings = settings.update(new_settings)
            
            # Update monitor settings if it exists
            if monitor:
                monitor.update_settings(
                    scan_interval=settings.scan_interval,
                    distance_threshold=settings.distance_threshold
                )
            
            return jsonify({
                "message": "Settings updated successfully",
                "settings": updated_settings
            })
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
