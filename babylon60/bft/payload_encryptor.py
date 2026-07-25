import os
from cryptography.fernet import Fernet

class PayloadEncryptor:
    def __init__(self) -> None:
        vault_key = os.environ.get('CORTEX_VAULT_KEY')
        self._fernet = Fernet(vault_key.encode('utf-8')) if vault_key else None
    
    def encrypt(self, payload_json: str) -> str:
        if self._fernet:
            encrypted = self._fernet.encrypt(payload_json.encode('utf-8')).decode('utf-8')
            return f'C5ENC:{encrypted}'
        return payload_json
