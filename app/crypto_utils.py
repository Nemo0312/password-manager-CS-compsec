from cryptography.fernet import Fernet
import base64
import os

# Generate a key or use an existing one
env_key = os.environ.get("MASTER_KEY")
SECRET_KEY = env_key.encode() if env_key else Fernet.generate_key()
fernet = Fernet(SECRET_KEY)


def encrypt_entry(site: str, username: str, password: str) -> dict:
    return {
        "site": fernet.encrypt(site.encode()).decode(),
        "username": fernet.encrypt(username.encode()).decode(),
        "password": fernet.encrypt(password.encode()).decode()
    }

def decrypt_entry(entry: dict) -> tuple:
    return (
        fernet.decrypt(entry["site"].encode()).decode(),
        fernet.decrypt(entry["username"].encode()).decode(),
        fernet.decrypt(entry["password"].encode()).decode()
    )
