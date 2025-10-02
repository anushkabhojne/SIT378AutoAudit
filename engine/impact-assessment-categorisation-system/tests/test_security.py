import unittest
from security.credential_manager import CredentialManager
from security.encryption import EncryptionManager
from cryptography.fernet import Fernet

class TestCredentialManager(unittest.TestCase):
    def setUp(self):
        self.key = Fernet.generate_key()
        self.cm = CredentialManager(encryption_key = self.key, credential_store_path = ":memory:")

    def test_add_and_get_credential(self):
        self.cm.add_credential('test_key', 'secret')
        cred = self.cm.get_credential('test_key')
        self.assertEqual(cred, 'secret')

    def test_remove_credential(self):
        self.cm.add_credential('test_key', 'secret')
        self.cm.remove_credential('test_key')
        cred = self.cm.get_credential('test_key')
        self.assertIsNone(cred)

class TestEncryptionManager(unittest.TestCase):
    
    def setUp(self):
        self.key = Fernet.generate_key()
        self.em = EncryptionManager(self.key)

    def test_encrypt_decrypt(self):
        data = b"test data"
        encrypted = self.em.encrypt(data)
        decrypted = self.em.decrypt(encrypted)
        self.assertEqual(decrypted, data)

if __name__ == '__main__':
    unittest.main()
