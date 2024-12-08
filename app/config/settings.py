class Settings:
    """Manages application settings with validation"""
    
    def __init__(self):
        self._settings = {
            "scan_interval": 2,
            "distance_threshold": 10
        }

    def get_all(self):
        """Get all current settings"""
        return self._settings.copy()

    def update(self, new_settings):
        """Update settings with validation"""
        if not isinstance(new_settings.get('scan_interval'), (int, float)) or \
           not isinstance(new_settings.get('distance_threshold'), (int, float)):
            raise ValueError("Invalid settings format")
        
        self._settings.update(new_settings)
        return self._settings.copy()

    def get(self, key, default=None):
        """Get a specific setting value"""
        return self._settings.get(key, default)

    @property
    def scan_interval(self):
        return self._settings['scan_interval']

    @property
    def distance_threshold(self):
        return self._settings['distance_threshold']

# Create a global settings instance
settings = Settings()
