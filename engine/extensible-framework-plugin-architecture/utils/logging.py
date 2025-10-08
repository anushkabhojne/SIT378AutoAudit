"""
Logging Utilities

Configures logging for the Compliance Framework Engine.

Author: Senior Lead, AutoAudit
"""

import logging

def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Set up logging configuration.

    :param level: Logging level as string.
    :param log_file: Optional log file path.
    
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level = log_level,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = handlers
    )
