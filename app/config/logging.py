import logging

class ColoredFormatter(logging.Formatter):
    """A custom formatter that adds ANSI color codes to log messages based on their level.
    
    This formatter enhances log readability by color-coding different log levels:
    - DEBUG: Blue
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red

    Inherits from logging.Formatter and overrides the format method to add color.
    """

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
        """Format the log record with appropriate color codes.

        Args:
            record: A LogRecord instance representing the event being logged.

        Returns:
            str: The formatted log message with color codes.

        Note:
            The method preserves the original message and level name, restoring them
            after formatting to prevent any side effects on other formatters.
        """
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
    """Configure and initialize application-wide logging settings.

    This function sets up:
    - Root logger with DEBUG level
    - Console handler with colored formatting
    - Custom format including timestamp, logger name, level, and message

    Returns:
        logging.Logger: A configured logger instance for the current module.

    Example:
        logger = setup_logging()
        logger.info("Application started")
    """
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
