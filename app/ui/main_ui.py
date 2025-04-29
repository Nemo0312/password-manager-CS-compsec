import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Input, Button, Static, DataTable
from app.crypto.crypto_utils import encrypt, decrypt

VAULT_PATH = Path("app/data/vault.json")

class PasswordManagerApp(App):
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Input(placeholder="Master Password", id="master"),
            Input(placeholder="Service Name", id="service"),
            Input(placeholder="Username", id="username"),
            Input(placeholder="Password", id="password"),
            Button("Save Entry", id="save"),
            Button("Load Vault", id="load"),
            Static("", id="status"),
            DataTable(id="vault_table"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        master = self.query_one("#master", Input).value
        status = self.query_one("#status", Static)
        table = self.query_one("#vault_table", DataTable)
        table.clear(columns=True)

        if event.button.id == "save":
            entry = {
                "service": self.query_one("#service", Input).value,
                "username": self.query_one("#username", Input).value,
                "password": self.query_one("#password", Input).value,
            }
            encrypted = encrypt(master, json.dumps(entry))
            data = []
            if VAULT_PATH.exists():
                with open(VAULT_PATH, "r") as f:
                    data = json.load(f)
            data.append(encrypted)
            with open(VAULT_PATH, "w") as f:
                json.dump(data, f)
            status.update("Entry Saved.")

        elif event.button.id == "load":
            if not VAULT_PATH.exists():
                status.update("No vault found.")
                return
            with open(VAULT_PATH, "r") as f:
                data = json.load(f)
            table.add_columns("Service", "Username", "Password")
            for record in data:
                try:
                    entry = json.loads(decrypt(master, record))
                    table.add_row(entry["service"], entry["username"], entry["password"])
                except Exception as e:
                    status.update("Decryption failed.")
