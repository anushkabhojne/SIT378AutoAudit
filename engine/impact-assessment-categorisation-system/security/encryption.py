"""
Encryption Module

Provides encryption and decryption utilities using Fernet symmetric encryption.

Author: Senior Lead, AutoAudit
"""

from cryptography.fernet import Fernet

class EncryptionManager:
    
    def __init__(self, key: bytes):
        """
        Initialise the EncryptionManager with a symmetric key.

        :param key: A bytes object representing the Fernet key.
        """
        
        self._fernet = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt the given data.

        :param data: Data to encrypt as bytes.
        :return: Encrypted data as bytes.
        """
        
        return self._fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """
        Decrypt the given token.

        :param token: Encrypted data as bytes.
        :return: Decrypted data as bytes.
        """
        
        return self._fernet.decrypt(token)
