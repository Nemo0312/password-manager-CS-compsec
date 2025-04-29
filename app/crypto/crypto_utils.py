import os
import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(password.encode())

def encrypt(password: str, plaintext: str) -> dict:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return {
        "salt": urlsafe_b64encode(salt).decode(),
        "nonce": urlsafe_b64encode(nonce).decode(),
        "ciphertext": urlsafe_b64encode(ciphertext).decode()
    }

def decrypt(password: str, data: dict) -> str:
    salt = urlsafe_b64decode(data["salt"])
    nonce = urlsafe_b64decode(data["nonce"])
    ciphertext = urlsafe_b64decode(data["ciphertext"])
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
