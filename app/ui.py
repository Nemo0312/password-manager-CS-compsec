from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Button, DataTable
from textual.containers import Vertical, Horizontal
from storage import load_data, save_data
from crypto_utils import encrypt_entry, decrypt_entry


class PasswordManagerApp(App):
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        self.input_site = Input(placeholder="Site", id="site")
        self.input_username = Input(placeholder="Username", id="username")
        self.input_password = Input(placeholder="Password", id="password")
        self.table = DataTable(id="entries")
        self.table.add_columns("Site", "Username", "Password")

        yield Vertical(
            Static("Password Manager", id="title"),
            Horizontal(self.input_site, self.input_username, self.input_password),
            Button(label="Add", id="add"),
            self.table,
        )

    def on_button_pressed(self, event):
        if event.button.id == "add":
            site = self.input_site.value
            username = self.input_username.value
            password = self.input_password.value
            encrypted = encrypt_entry(site, username, password)
            data = load_data()
            data.append(encrypted)
            save_data(data)
            self.refresh_table()

    def on_mount(self):
        self.refresh_table()

    def refresh_table(self):
        self.table.clear()
        for entry in load_data():
            site, user, pwd = decrypt_entry(entry)
            self.table.add_row(site, user, pwd)
