# tpi-apis/logging.py
"""
Centralized logging configuration for the TPI API.
"""
import logging
import sys

# Define the log format
LOG_FORMAT = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler 
console_handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

file_handler = logging.FileHandler('tpi_api.log')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger instance with the specified name.
    """
    return logging.getLogger(name)

# Example usage (optional, just for testing this file)
# if __name__ == "__main__":
#     logger = get_logger(__name__)
#     logger.debug("This is a debug message.")
#     logger.info("This is an info message.")
#     logger.warning("This is a warning message.")
#     logger.error("This is an error message.")
#     logger.critical("This is a critical message.")
