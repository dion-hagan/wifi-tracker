import logging

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    
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
        color = self.COLORS.get(record.levelname, self.COLORS['NOTSET'])
        reset = self.COLORS['RESET']

        original_msg = record.msg
        original_levelname = record.levelname

        try:
            record.msg = f"{color}{original_msg}{reset}"
            record.levelname = f"{color}{original_levelname}{reset}"
            formatted_message = super().format(record)
            return formatted_message
        except Exception:
            return super().format(record)
        finally:
            record.msg = original_msg
            record.levelname = original_levelname

def setup_logging():
    """Configure application-wide logging settings"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(colored_formatter)

    root_logger.handlers = []
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)
