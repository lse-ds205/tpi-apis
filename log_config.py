# tpi-apis/logging.py
import logging
import sys

# Define the log format
LOG_FORMAT = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,        # Set the default level
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    stream=sys.stdout,         # Log to standard output
    # filename='api.log',      # Uncomment to log to a file instead/as well
)

# Function to get a logger instance
def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance with the specified name."""
    return logging.getLogger(name)

# Example usage (optional, just for testing this file)
# if __name__ == "__main__":
#     logger = get_logger(__name__)
#     logger.info("Logging configured successfully.")
#     logger.warning("This is a warning message.")
#     logger.error("This is an error message.")
