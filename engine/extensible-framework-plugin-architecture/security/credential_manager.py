"""
Credential Manager

Manages credentials securely for the Compliance Framework Engine.

Author: Senior Lead, AutoAudit
"""

import os
import base64
import json
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from .encryption import EncryptionManager
import logging

class CredentialManager:
    
    def __init__(self, encryption_key: Optional[bytes] = None, credential_store_path: str = "credentials.json"):
        
        self._logger = logging.getLogger(self.__class__.__name__)
        self._credential_store_path = credential_store_path
        
        if encryption_key is None:
            self._logger.warning("No encryption key provided, generating a new one")
            self._encryption_key = Fernet.generate_key()
        
        else:
            self._encryption_key = encryption_key
        
        self._encryption_manager = EncryptionManager(self._encryption_key)
        self._credentials = self._load_credentials()

    def _load_credentials(self) -> dict:
        
        if not os.path.exists(self._credential_store_path):
            self._logger.info("Credential store not found, starting with empty store")
            return {}
        
        try:
            
            with open(self._credential_store_path, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self._encryption_manager.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode("utf-8"))
            self._logger.info("Credentials loaded successfully")
            return credentials
        
        except (IOError, InvalidToken, json.JSONDecodeError) as e:
            self._logger.error(f"Failed to load credentials: {e}")
            return {}

    def _save_credentials(self):
        
        try:
            data = json.dumps(self._credentials).encode("utf-8")
            encrypted_data = self._encryption_manager.encrypt(data)
        
            with open(self._credential_store_path, "wb") as f:
                f.write(encrypted_data)
        
            self._logger.info("Credentials saved successfully")
        
        except IOError as e:
            self._logger.error(f"Failed to save credentials: {e}")

    def add_credential(self, key: str, credential: str):
        self._credentials[key] = credential
        self._save_credentials()
        self._logger.debug(f"Credential added for key: {key}")

    def get_credential(self, key: str) -> Optional[str]:
        return self._credentials.get(key)

    def remove_credential(self, key: str):
        
        if key in self._credentials:
            del self._credentials[key]
            self._save_credentials()
            self._logger.debug(f"Credential removed for key: {key}")
