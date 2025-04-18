import logging
import sys


def setup_logger(name='app', level=logging.INFO):
    """Set up and return a logger with the specified name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()

# Export the logger
__all__ = ['logger', 'setup_logger']
