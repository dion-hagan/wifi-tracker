class Settings:
    """Manages application settings with validation and type checking.

    This class provides a centralized way to manage application settings with
    built-in validation. It maintains settings for scan intervals and distance
    thresholds, ensuring type safety and providing convenient access methods.

    Attributes:
        _settings (dict): Internal dictionary storing the application settings
            - scan_interval: Time between device scans in seconds
            - distance_threshold: Maximum distance in meters for device tracking
    """
    
    def __init__(self):
        """Initialize default settings values."""
        self._settings = {
            "scan_interval": 2,
            "distance_threshold": 10
        }

    def get_all(self):
        """Retrieve all current settings.

        Returns:
            dict: A copy of all current settings to prevent direct modification
                 of internal settings dictionary.
        """
        return self._settings.copy()

    def update(self, new_settings):
        """Update settings with validation.

        Args:
            new_settings (dict): Dictionary containing new setting values.
                Must include numeric values for 'scan_interval' and 'distance_threshold'.

        Returns:
            dict: A copy of the updated settings dictionary.

        Raises:
            ValueError: If the new settings contain invalid types or missing required fields.
        """
        if not isinstance(new_settings.get('scan_interval'), (int, float)) or \
           not isinstance(new_settings.get('distance_threshold'), (int, float)):
            raise ValueError("Invalid settings format")
        
        self._settings.update(new_settings)
        return self._settings.copy()

    def get(self, key, default=None):
        """Get a specific setting value.

        Args:
            key (str): The setting key to retrieve.
            default: The value to return if the key doesn't exist.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        return self._settings.get(key, default)

    @property
    def scan_interval(self):
        """Get the current scan interval setting.

        Returns:
            float: The time interval between device scans in seconds.
        """
        return self._settings['scan_interval']

    @property
    def distance_threshold(self):
        """Get the current distance threshold setting.

        Returns:
            float: The maximum distance in meters for device tracking.
        """
        return self._settings['distance_threshold']

# Create a global settings instance
settings = Settings()
