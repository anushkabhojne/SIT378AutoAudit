"""
Validation Utilities

Provides validation functions for input data.

Author: Senior Lead, AutoAudit
"""

import re

def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    :param email: Email string.
    :return: True if valid, False otherwise.
    """
    
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_valid_ip(ip: str) -> bool:
    """
    Validate IPv4 address format.

    :param ip: IP address string.
    :return: True if valid, False otherwise.
    """
    
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    
    if re.match(pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    return False
