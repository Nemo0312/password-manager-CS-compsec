import json
import pyperclip
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Button, Static, DataTable, Label
from app.crypto.crypto_utils import encrypt, decrypt
from app.p2p.p2p import share_password, receive_password

VAULT_PATH = Path("app/data/vault.json")

class PasswordManagerApp(App):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(
            Label("Vault Entry"),
            Input(placeholder="Master Password", id="master", password=True),
            Input(placeholder="Service Name", id="service"),
            Input(placeholder="Username", id="username"),
            Input(placeholder="Password", id="password", password=True),
            Horizontal(
                Button("Save Entry", id="save"),
                Button("Load Vault", id="load"),
            ),
            Label("Share/Receive Password (TLS P2P)"),
            Input(placeholder="Peer IP (default 127.0.0.1)", id="peer_ip"),
            Input(placeholder="Port (default 65432)", id="peer_port"),
            Horizontal(
                Button("Share Entry", id="share"),
                Button("Receive Entry", id="receive"),
            ),
            Static("App loaded. Click buttons to interact.", id="status"),
            DataTable(id="vault_table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#vault_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

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
            if not entry["service"] or not entry["password"]:
                status.update("[Error] Service and Password are required.")
                return
            encrypted = encrypt(master, json.dumps(entry))
            data = []
            VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
            if VAULT_PATH.exists():
                with open(VAULT_PATH, "r") as f:
                    data = json.load(f)
            data.append(encrypted)
            with open(VAULT_PATH, "w") as f:
                json.dump(data, f)
            status.update("Entry saved successfully.")

        elif event.button.id == "load":
            if not VAULT_PATH.exists():
                status.update("[Error] No vault found.")
                return
            with open(VAULT_PATH, "r") as f:
                data = json.load(f)
            table.add_columns("Service", "Username", "Password")
            for record in data:
                try:
                    entry = json.loads(decrypt(master, record))
                    table.add_row(entry["service"], entry["username"], entry["password"])
                except Exception:
                    status.update("[Error] Decryption failed.")
                    return
            status.update("Vault loaded successfully.")

        elif event.button.id == "share":
            service = self.query_one("#service", Input).value
            username = self.query_one("#username", Input).value
            password_value = self.query_one("#password", Input).value
            peer_ip = self.query_one("#peer_ip", Input).value or "127.0.0.1"
            peer_port = int(self.query_one("#peer_port", Input).value or 65432)
            payload = json.dumps({
                "service": service,
                "username": username,
                "password": password_value
            })
            try:
                share_password(payload, host=peer_ip, port=peer_port)
                status.update(f"Password shared to {peer_ip}:{peer_port}.")
            except ConnectionRefusedError:
                status.update(f"[Error] Connection refused by {peer_ip}:{peer_port}.")
            except TimeoutError:
                status.update(f"[Error] Connection to {peer_ip}:{peer_port} timed out.")
            except Exception as e:
                status.update(f"[Error] {str(e)}")

        elif event.button.id == "receive":
            port = int(self.query_one("#peer_port", Input).value or 65432)
            try:
                received = receive_password(port=port)
                if received:
                    try:
                        entry = json.loads(received)
                        self.query_one("#service", Input).value = entry.get("service", "")
                        self.query_one("#username", Input).value = entry.get("username", "")
                        self.query_one("#password", Input).value = entry.get("password", "")
                        status.update("Password received successfully.")
                    except json.JSONDecodeError:
                        status.update("[Error] Invalid data received.")
                else:
                    status.update("[Error] No data received.")
            except OSError as e:
                status.update(f"[Error] Receive failed: {str(e)}")
            except Exception as e:
                status.update(f"[Error] {str(e)}")

    def on_data_table_row_selected(self, message: DataTable.RowSelected) -> None:
        table = self.query_one("#vault_table", DataTable)
        status = self.query_one("#status", Static)
        if message.row_key is not None:
            row = table.get_row(message.row_key)
            pyperclip.copy(row[-1])
            status.update(f"Password for {row[0]} copied to clipboard.")