
import json  # For handling JSON read/write
import pyperclip  # For clipboard support
from pathlib import Path  # For file paths
from typing import Dict, Optional, Tuple, Any  # For type hints
from uuid import uuid4  # For generating unique confirmation IDs

from textual.app import App, ComposeResult  # Main app structure
from textual.containers import Horizontal, Vertical  # Layout controls
from textual.widgets import Header, Footer, Input, Button, Static, DataTable, Label  # UI elements
from textual.validation import Number  # For port validation

# Import encryption/decryption functions (assumed to exist)
from app.crypto.crypto_utils import encrypt, decrypt
# Import TLS-based sharing methods (assumed to exist)
from app.p2p.p2p import share_password, receive_password

# Define vault file location
VAULT_PATH = Path("app/data/vault.json")

class PasswordManagerApp(App):
    """Textual TUI application for managing encrypted passwords with P2P sharing."""

    CSS = """
    Screen {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    #main_container {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }

    #left_panel, #right_panel {
        height: 100%;
        padding: 1;
    }

    #left_panel {
        width: 50%;
        border: round $primary;
        overflow-y: auto;
    }

    #right_panel {
        width: 50%;
        border: round $secondary;
        overflow-y: auto;
    }

    Vertical {
        width: 100%;
    }

    Horizontal {
        width: 100%;
        height: auto;  /* Fix button disappearing */
        padding: 0 0 1 0;
    }

    Input, Label, Static {
        width: 100%;
        margin: 1 0;
    }

    Button {
        width: auto;
        min-width: 12;  /* Optional: constrain minimum size */
        max-width: 24;  /* Optional: avoid stretching */
    }

    #confirm.hidden, #cancel.hidden {
        display: none;
    }

    #status {
        padding: 1;
        background: $surface;
        color: $text;
        height: auto;
        overflow: auto;
    }

    #vault_table {
        height: 1fr;
        overflow: auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the app with confirmation state."""
        super().__init__(**kwargs)
        self._confirm_state: Optional[Tuple[str, str, Any]] = None  # Stores (action, confirm_id, data)

    def compose(self) -> ComposeResult:
        yield Header()

        yield Horizontal(  # Split screen layout
            Vertical(  # Left panel
                Label("Master Password"),
                Input(placeholder="Enter Master Password (8 letter Min)", id="master", password=True),

                Label("Vault Entry"),
                Input(placeholder="Service Name", id="service"),
                Input(placeholder="Username", id="username"),
                Input(placeholder="Password", id="password", password=True),

                Label("Controls"),
                Horizontal(
                    Button("Show/Hide", id="toggle_password", variant="default"),
                    Button("Save", id="save", variant="success"),
                    Button("Load", id="load", variant="primary"),
                    Button("Reset", id="reset", variant="warning"),
                    Button("Clear Vault", id="clear_vault", variant="error"),
                    Button("Copy Table", id="copy_table"),
                ),
                Horizontal(
                    Button("Confirm", id="confirm", classes="hidden"),
                    Button("Cancel", id="cancel", classes="hidden"),
                ),

                Label("P2P Share/Receive"),
                Input(placeholder="Peer IP (127.0.0.1)", id="peer_ip"),
                Input(placeholder="Port (65432)", id="peer_port"),
                
                Horizontal(
                    Button("Share", id="share", variant="primary"),
                    Button("Receive", id="receive", variant="primary"),
                    Button("Help", id="help"),
                ),

                Static("Status: Ready", id="status"),

                id="left_panel"
            ),

            Vertical(  # Right panel
                Label("Vault Entries"),
                DataTable(id="vault_table", show_header=True, zebra_stripes=True),
                id="right_panel"
            ),

            id="main_container"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the vault table on app start."""
        table = self.query_one("#vault_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Service", "Username", "Password")  # Initialize table columns

    def get_input_values(self) -> Dict[str, str]:
        """Helper method to retrieve values from input fields."""
        return {
            "master": self.query_one("#master", Input).value.strip(),
            "service": self.query_one("#service", Input).value.strip(),
            "username": self.query_one("#username", Input).value.strip(),
            "password": self.query_one("#password", Input).value.strip(),
            "peer_ip": self.query_one("#peer_ip", Input).value.strip() or "127.0.0.1",
            "peer_port": self.query_one("#peer_port", Input).value.strip() or "65432",
        }

    def update_status(self, message: str) -> None:
        """Helper method to update the status widget."""
        self.query_one("#status", Static).update(message)

    def toggle_confirm_button(self, show: bool) -> None:
        """Show or hide the Confirm and Cancel buttons with error handling."""
        try:
            confirm_button = self.query_one("#confirm", Button)
            cancel_button = self.query_one("#cancel", Button)
            confirm_button.classes = [] if show else ["hidden"]
            cancel_button.classes = [] if show else ["hidden"]
        except NoMatches:
            self.update_status("[Error] Confirmation or Cancel button not found.")
        except Exception as e:
            self.update_status(f"[Error] Failed to toggle confirmation buttons: {str(e)}")

    def validate_port(self, port_str: str) -> Optional[int]:
        """Validate that the port is a number between 1 and 65535."""
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return port
            self.update_status("[Error] Port must be between 1 and 65535.")
            return None
        except ValueError:
            self.update_status("[Error] Port must be a valid number.")
            return None

    def check_service_exists(self, service: str, data: list) -> bool:
        """Check if a service name already exists in the vault."""
        for record in data:
            try:
                entry = json.loads(decrypt(self.get_input_values()["master"], record))
                if entry.get("service") == service:
                    return True
            except Exception:
                continue
        return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        inputs = self.get_input_values()

        if button_id == "save":
            self.handle_save_entry(inputs)
        elif button_id == "load":
            self.handle_load_vault(inputs["master"])
        elif button_id == "share":
            self.handle_share_entry(inputs)
        elif button_id == "receive":
            self.handle_receive_entry(inputs["peer_port"])
        elif button_id == "reset":
            self.handle_reset_form()
        elif button_id == "help":
            self.handle_show_help()
        elif button_id == "copy_table":
            self.handle_copy_table()
        elif button_id == "toggle_password":
            self.handle_toggle_password()
        elif button_id == "clear_vault":
            self.handle_clear_vault()
        elif button_id == "confirm":
            self.handle_confirm()
        elif button_id == "cancel":
            self.handle_cancel()

    def handle_save_entry(self, inputs: Dict[str, str]) -> None:
        """Handle saving a new vault entry with confirmation."""
        if not inputs["service"] or not inputs["password"]:
            self.update_status("[Error] Service and Password are required.")
            return
        if len(inputs["master"]) < 8:
            self.update_status("[Error] Master password must be at least 8 characters.")
            return

        entry = {
            "service": inputs["service"],
            "username": inputs["username"],
            "password": inputs["password"],
        }
        data = []
        VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if VAULT_PATH.exists():
            try:
                with open(VAULT_PATH, "r") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                self.update_status("[Error] Vault file is corrupted.")
                return

        # Check for duplicate service name
        if self.check_service_exists(inputs["service"], data):
            confirm_id = str(uuid4())
            self._confirm_state = ("save", confirm_id, entry)
            self.update_status(
                f"Service '{inputs['service']}' already exists. Click Confirm to overwrite or Cancel to abort."
            )
            self.toggle_confirm_button(True)
            return

        # Save the entry
        encrypted = encrypt(inputs["master"], json.dumps(entry))
        data.append(encrypted)
        with open(VAULT_PATH, "w") as f:
            json.dump(data, f)
        self.update_status("Entry saved successfully.")
        self.query_one("#master", Input).value = ""  # Clear master password

    def handle_clear_vault(self) -> None:
        """Handle initiating the vault clear action with confirmation."""
        if not VAULT_PATH.exists():
            self.update_status("[Error] No vault found to clear.")
            return

        confirm_id = str(uuid4())
        self._confirm_state = ("clear", confirm_id, None)
        self.update_status(
            "Are you sure you want to clear the vault? Click Confirm to proceed or Cancel to abort."
        )
        self.toggle_confirm_button(True)

    def handle_confirm(self) -> None:
        """Handle confirmation for save or clear actions."""
        if not self._confirm_state:
            self.update_status("[Error] No confirmation action pending.")
            self.toggle_confirm_button(False)
            return

        action, confirm_id, data = self._confirm_state
        self._confirm_state = None
        self.toggle_confirm_button(False)

        if action == "save" and data:
            try:
                vault_data = []
                if VAULT_PATH.exists():
                    with open(VAULT_PATH, "r") as f:
                        vault_data = json.load(f)
                encrypted = encrypt(self.get_input_values()["master"], json.dumps(data))
                vault_data.append(encrypted)
                with open(VAULT_PATH, "w") as f:
                    json.dump(vault_data, f)
                self.update_status("Entry overwritten successfully.")
                self.query_one("#master", Input).value = ""
            except json.JSONDecodeError:
                self.update_status("[Error] Vault file is corrupted.")
            except Exception as e:
                self.update_status(f"[Error] Failed to save entry: {str(e)}")

        elif action == "clear":
            try:
                # Clear the vault file by writing an empty list
                with open(VAULT_PATH, "w") as f:
                    json.dump([], f)
                # Clear the table
                table = self.query_one("#vault_table", DataTable)
                table.clear()
                self.update_status("Vault cleared successfully.")
            except Exception as e:
                self.update_status(f"[Error] Failed to clear vault: {str(e)}")

    def handle_cancel(self) -> None:
        """Handle canceling a confirmation action."""
        self._confirm_state = None
        self.toggle_confirm_button(False)
        self.update_status("Confirmation canceled.")

    def handle_load_vault(self, master: str) -> None:
        """Handle loading and decrypting vault entries."""
        if not master:
            self.update_status("[Error] Master password is required.")
            return
        if len(master) < 8:
            self.update_status("[Error] Master password must be at least 8 characters.")
            return
        if not VAULT_PATH.exists():
            self.update_status("[Error] No vault found.")
            return

        table = self.query_one("#vault_table", DataTable)
        table.clear()  # Clear rows but keep columns
        try:
            with open(VAULT_PATH, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            self.update_status("[Error] Vault file is corrupted.")
            return

        errors = 0
        for record in data:
            try:
                entry = json.loads(decrypt(master, record))
                table.add_row(entry["service"], entry["username"], entry["password"])
            except Exception:
                errors += 1
        if errors == len(data):
            self.update_status("[Error] Decryption failed for all entries.")
        elif errors > 0:
            self.update_status(f"Loaded vault with {errors} decryption errors.")
        else:
            self.update_status("Vault loaded successfully.")
        self.query_one("#master", Input).value = ""

    def handle_share_entry(self, inputs: Dict[str, str]) -> None:
        """Handle sharing an entry via P2P."""
        port = self.validate_port(inputs["peer_port"])
        if not port:
            return
        if not inputs["service"] or not inputs["password"]:
            self.update_status("[Error] Service and Password are required.")
            return

        self.update_status("Sharing password... (please wait)")
        payload = json.dumps({
            "service": inputs["service"],
            "username": inputs["username"],
            "password": inputs["password"],
        })
        try:
            share_password(payload, host=inputs["peer_ip"], port=port)
            self.update_status(f"Password shared to {inputs['peer_ip']}:{port}.")
        except ConnectionRefusedError:
            self.update_status(f"[Error] Connection refused by {inputs['peer_ip']}:{port}.")
        except TimeoutError:
            self.update_status(f"[Error] Connection to {inputs['peer_ip']}:{port} timed out.")
        except Exception as e:
            self.update_status(f"[Error] Share failed: {str(e)}")

    def handle_receive_entry(self, port_str: str) -> None:
        """Handle receiving an entry via P2P."""
        port = self.validate_port(port_str)
        if not port:
            return

        self.update_status("Waiting to receive password... (please wait)")
        try:
            received = receive_password(port=port)
            if received:
                try:
                    entry = json.loads(received)
                    self.query_one("#service", Input).value = entry.get("service", "")
                    self.query_one("#username", Input).value = entry.get("username", "")
                    self.query_one("#password", Input).value = entry.get("password", "")
                    self.update_status("Password received successfully.")
                except json.JSONDecodeError:
                    self.update_status("[Error] Invalid data received.")
            else:
                self.update_status("[Error] No data received.")
        except OSError as e:
            self.update_status(f"[Error] Receive failed: {str(e)}")
        except Exception as e:
            self.update_status(f"[Error] Receive failed: {str(e)}")

    def handle_reset_form(self) -> None:
        """Handle resetting all input fields."""
        for field in ["master", "service", "username", "password", "peer_ip", "peer_port"]:
            self.query_one(f"#{field}", Input).value = ""
        self.update_status("Form reset.")
        self.toggle_confirm_button(False)  # Hide Confirm button if visible
        self._confirm_state = None  # Clear confirmation state

    def handle_show_help(self) -> None:
        """Handle displaying help instructions."""
        help_text = (
            "[Help]\n"
            "- Enter a Master Password (min 8 chars) to encrypt/decrypt vault entries.\n"
            "- Save entries with Service, Username, and Password.\n"
            "- Load Vault to decrypt and view stored passwords.\n"
            "- Share and Receive allow P2P encrypted password transfer.\n"
            "- Click a vault row to copy the password.\n"
            "- Copy Table copies all entries to clipboard.\n"
            "- Clear Vault deletes all stored entries (requires clicking Confirm or Cancel to abort).\n"
            "- Toggle Password Visibility shows/hides the password field.\n"
            "- Use Reset to clear the form and cancel confirmations.\n"
        )
        self.update_status(help_text)

    def handle_copy_table(self) -> None:
        """Handle copying the entire table to the clipboard."""
        table = self.query_one("#vault_table", DataTable)
        if not table.row_count:
            self.update_status("[Error] Table is empty.")
            return

        table_data = []
        for row_key in table.rows.keys():
            # Use get_row to retrieve the cell values as a list
            row_cells = table.get_row(row_key)
            table_data.append("\t".join(str(cell) for cell in row_cells))
        table_text = "\n".join(table_data)
        try:
            pyperclip.copy(table_text)
            self.update_status("Table copied to clipboard.")
        except Exception as e:
            self.update_status(f"[Error] Clipboard copy failed: {str(e)}")

    def handle_toggle_password(self) -> None:
        """Handle toggling password field visibility."""
        password_input = self.query_one("#password", Input)
        password_input.password = not password_input.password
        self.update_status(
            "Password field is now " + ("hidden" if password_input.password else "visible")
        )

    def on_data_table_row_selected(self, message: DataTable.RowSelected) -> None:
        """Copy password to clipboard when a table row is selected."""
        table = self.query_one("#vault_table", DataTable)
        if message.row_key is not None:
            row = table.get_row(message.row_key)
            try:
                pyperclip.copy(row[-1])
                self.update_status(f"Password for {row[0]} copied to clipboard.")
            except Exception as e:
                self.update_status(f"[Error] Clipboard copy failed: {str(e)}")