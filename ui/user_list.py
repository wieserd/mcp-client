"""User and room occupant sidebar widget for MCP client."""

from __future__ import annotations
from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Static


class UserListSidebar(Vertical):
    """Sidebar displaying active users, players, and room occupants."""

    DEFAULT_CSS = """
    UserListSidebar {
        width: 26;
        height: 1fr;
        background: #151515;
        border: round #4a4a4a;
        padding: 0 1;
    }
    UserListSidebar.hidden {
        display: none;
    }
    #user_list_header {
        color: #00ffff;
        text-style: bold;
        border-bottom: solid #333333;
        margin-bottom: 1;
        height: auto;
    }
    #user_list_body {
        height: 1fr;
        overflow-y: auto;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._users: set[str] = set()

    def compose(self):
        yield Static("Users (0)", id="user_list_header")
        yield Static("No users online", id="user_list_body")

    def _refresh_display(self) -> None:
        try:
            header = self.query_one("#user_list_header", Static)
            body = self.query_one("#user_list_body", Static)
        except Exception:
            return

        count = len(self._users)
        header.update(f"Users ({count})")

        if not self._users:
            body.update("[dim]No users detected[/dim]")
            return

        lines = [f"[bold green]●[/] [cyan]{u}[/]" for u in sorted(self._users)]
        body.update("\n".join(lines))

    def add_user(self, name: str) -> bool:
        """Adds a user to the active list."""
        cleaned = name.strip()
        if not cleaned or cleaned in self._users:
            return False
        self._users.add(cleaned)
        self._refresh_display()
        return True

    def remove_user(self, name: str) -> bool:
        """Removes a user from the active list."""
        cleaned = name.strip()
        for u in list(self._users):
            if u.lower() == cleaned.lower():
                self._users.remove(u)
                self._refresh_display()
                return True
        return False

    def set_users(self, names: list[str]) -> None:
        """Sets the full list of users."""
        self._users = {n.strip() for n in names if n.strip()}
        self._refresh_display()

    def clear_users(self) -> None:
        """Clears all users."""
        self._users.clear()
        self._refresh_display()

    def get_users(self) -> list[str]:
        """Returns the list of current users."""
        return sorted(self._users)

    def toggle(self) -> bool:
        """Toggles sidebar visibility and returns new visibility state."""
        self.toggle_class("hidden")
        return not self.has_class("hidden")
