# Decentralized Password Manager (TUI + P2P)

A lightweight, fully local, decentralized Password Manager built with [Textual](https://github.com/Textualize/textual) (TUI framework) and secured with AES-GCM encryption.  
Supports basic P2P password sharing and click-to-copy functionality.

## Features

- Full encryption: AES-256 GCM with PBKDF2-HMAC key derivation.
- Local storage: No cloud, no web — passwords stored securely on your device.
- TUI (Terminal UI): Fast and minimal interface built with Textual.
- Click-to-copy: Click on an entry to copy the password to clipboard.
- P2P password sharing: Securely send/receive password entries over the network (basic TCP).
- Docker-ready: Easy containerized deployment with persistent storage.

## Setup

### Install Locally

```bash
git clone https://github.com/yourusername/password-manager.git
cd password-manager
pip install -r requirements.txt
python main.py
```

### Run with Docker

```bash
# Build the Docker image
docker build -t password-manager .

# Run and persist vault data
docker run -it -v $(pwd)/vault:/app/app/data password-manager
```

## Usage

1. Enter your Master Password to unlock/encrypt your vault.
2. Add Service Name, Username, and Password entries.
3. Save entries into the encrypted vault.
4. Load and view stored entries — click a row to instantly copy the password.
5. Share: Send an entry via P2P to another instance.
6. Receive: Accept an entry from another device securely.

## Security Design

- Encryption: AES-GCM (256-bit) + random salt/IV per entry.
- Key Derivation: PBKDF2 with SHA-256 (100,000 iterations).
- Persistence: Vault stored locally, encrypted in `vault.json`.
- P2P Sharing: Basic socket transfer (plaintext for now; should be used inside trusted networks).

Note: Future versions can encrypt the P2P transfer for even stronger security.

## Project Structure

```
app/
 ├── crypto/          # Encryption / decryption logic
 ├── data/            # Local vault storage
 ├── p2p/             # Peer-to-peer transfer logic
 └── ui/              # Textual terminal UI
Dockerfile
requirements.txt
main.py
```

## Tech Stack

- Python 3.11+
- Textual (TUI)
- Cryptography
- Pyperclip
- Docker

## Future Improvements

- Encrypted P2P password exchange
- Multi-user vault separation
- Auto-lock vault on idle
- Backup and restore vault
- LAN device discovery for easier sharing

## Credits

Built as a final project for our computer security course.
