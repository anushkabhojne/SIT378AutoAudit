"""
Retry Utilities

Provides retry decorators for function calls.

Author: Senior Lead, AutoAudit
"""

import time
import functools
import logging


def retry(exceptions, tries = 3, delay = 1, backoff = 2):
    """
    Retry decorator with exponential backoff.

    :param exceptions: Exception or tuple of exceptions to catch.
    :param tries: Number of attempts.
    :param delay: Initial delay between attempts.
    :param backoff: Backoff multiplier.
    """
    
    def decorator(func):
        @functools.wraps(func)
        
        def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            
            while _tries > 1:
                
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    logging.warning(f"{func.__name__} failed with {e}, retrying in {_delay} seconds...")
                    time.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
