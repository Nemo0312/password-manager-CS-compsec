# Decentralized Password Manager (TUI + P2P with TLS)

A local, decentralized Password Manager built with [Textual](https://github.com/Textualize/textual) and AES-256-GCM encryption.  
Supports TLS-encrypted P2P password sharing, click-to-copy functionality, and secure local storage.

## Features

- Full encryption: AES-256 GCM with PBKDF2-HMAC key derivation.
- Local storage: Passwords stored securely on your machine.
- TUI (Terminal UI): Fast, minimal, no bloat.
- Click-to-copy: Click table rows to copy passwords to clipboard.
- P2P password sharing: TLS-secured peer-to-peer sharing of password entries.
- Docker-ready: Simple containerized run with data persistence.

## Setup

### Local Run (Python)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/password-manager.git
cd password-manager
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python main.py
```

### Docker Run

1. Build the Docker image:

```bash
docker build -t password-manager .
```

2. Run the app with persistent vault:

```bash
docker run -it -v $(pwd)/vault:/app/app/data password-manager
```

> The `vault` folder on your machine will hold the encrypted password vault to persist data across container restarts.

## Usage Guide

1. **Master Password:**
   - First field: Your master password. This secures your vault.
   - Same master password is needed to decrypt later.

2. **Add an Entry:**
   - Fill out:
     - Service Name
     - Username
     - Password
   - Click `Save Entry`.

3. **Load Entries:**
   - Click `Load Vault` to decrypt and view all stored entries.
   - You can click a row in the table to instantly copy the password to your clipboard.

4. **TLS P2P Sharing:**
   - **Share:**
     - Fill Service, Username, Password fields.
     - Specify:
       - Peer IP (default `127.0.0.1`)
       - Port (default `65432`)
     - Click `Share Entry (TLS P2P)`.
   - **Receive:**
     - Specify Port (default `65432`).
     - Click `Receive Entry (TLS P2P)`.
     - Received entry will auto-fill the form fields.

## TLS Notes (P2P Sharing)

- The app auto-generates self-signed certificates (saved in `app/p2p/` as `cert.pem` and `key.pem`).
- All P2P communication is encrypted using TLS to protect sensitive data during transfer.
- Certificates are regenerated only if missing.

## Project Structure

```
app/
 ├── crypto/          # Encryption / decryption logic
 ├── data/            # Local vault storage
 ├── p2p/             # P2P logic with TLS
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

- Full certificate verification for P2P TLS
- Multi-user vault support
- Auto-lock on idle
- Encrypted backup & restore
- LAN peer discovery

## Credits

Developed as a final project for our computer security course.
