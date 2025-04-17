# 🔐 TUI Password Manager (Textual + Docker)

A simple terminal-based password manager built with [Textual](https://github.com/Textualize/textual) and Python.  
All passwords are AES-encrypted and stored locally in a JSON file.

---

## 🚀 Features

- Text User Interface (TUI) powered by Textual
- AES encryption using the `cryptography` library
- Add/view credentials: Site, Username, Password
- All data is encrypted and saved to `data/passwords.json`
- Dockerized development environment

---

## 📦 Requirements

- Docker (recommended)
- OR: Python 3.10+ with `pip`

---

## 🐳 Run With Docker

```bash
# Build the image
docker build -t password-manager .

# Run the app (persist data locally)
docker run --rm -it -v $(pwd)/data:/app/data password-manager
