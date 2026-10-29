"""Input handling, history support, and smart autocompletion for the MCP terminal client."""

from __future__ import annotations
from textual.binding import Binding
from textual.widgets import Input


SUBCOMMANDS: dict[str, list[str]] = {
    "log": ["on", "off", "status"],
    "macro": ["list", "set", "del"],
    "notify": ["on", "off", "sound", "watch", "unwatch", "list", "test"],
    "trigger": ["list", "add", "del", "toggle"],
    "ticker": ["list", "add", "del"],
    "users": ["list", "toggle", "add", "del", "clear"],
    "status": ["bar"],
}


class HistoryInput(Input):
    """An Input widget that supports cycling through command history and Tab autocompletion."""

    BINDINGS = [
        Binding("up", "history_up", "Previous command", show=False),
        Binding("down", "history_down", "Next command", show=False),
        Binding("escape", "clear_input", "Clear input", show=False),
        Binding("tab", "autocomplete", "Autocomplete", priority=True, show=True),
        Binding("ctrl+f", "app.toggle_search", "Search Scrollback", priority=True, show=False),
    ]

    def __init__(self, *args, max_history: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.history: list[str] = []
        self.history_index: int = -1
        self._draft: str = ""
        self.max_history = max_history

        # Autocompletion state
        self._tab_candidates: list[str] = []
        self._tab_index: int = -1
        self._tab_base: str = ""

    def _reset_tab_cycle(self) -> None:
        self._tab_candidates = []
        self._tab_index = -1
        self._tab_base = ""

    def _watch_value(self, value: str) -> None:
        super()._watch_value(value)
        # Reset tab cycle if input is manually edited
        if self._tab_candidates and self._tab_index != -1:
            expected = f"{self._tab_base}{self._tab_candidates[self._tab_index]} "
            expected_nospace = f"{self._tab_base}{self._tab_candidates[self._tab_index]}"
            if value != expected and value != expected_nospace:
                self._reset_tab_cycle()

    def add_history(self, text: str) -> None:
        """Adds a line to the command history."""
        cleaned = text.strip()
        if not cleaned:
            return

        # Avoid duplicate consecutive entries
        if not self.history or self.history[-1] != cleaned:
            self.history.append(cleaned)
            if len(self.history) > self.max_history:
                self.history.pop(0)

        self.history_index = -1
        self._draft = ""
        self._reset_tab_cycle()

    def action_history_up(self) -> None:
        """Cycle backwards to an older command."""
        if not self.history:
            return

        self._reset_tab_cycle()

        if self.history_index == -1:
            self._draft = self.value
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        self.value = self.history[self.history_index]
        self.cursor_position = len(self.value)

    def action_history_down(self) -> None:
        """Cycle forwards to a newer command or back to draft."""
        if not self.history or self.history_index == -1:
            return

        self._reset_tab_cycle()

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.value = self.history[self.history_index]
        else:
            self.history_index = -1
            self.value = self._draft

        self.cursor_position = len(self.value)

    def action_clear_input(self) -> None:
        """Clears the input bar and resets state."""
        self.value = ""
        self.history_index = -1
        self._draft = ""
        self._reset_tab_cycle()

    def _get_available_commands(self) -> list[str]:
        """Returns all built-in commands plus registered user macros."""
        commands = [
            "clear",
            "connect",
            "disconnect",
            "find",
            "help",
            "log",
            "macro",
            "notify",
            "quit",
            "reconnect",
            "search",
            "status",
            "ticker",
            "trigger",
            "users",
        ]
        macros_mgr = getattr(self.app, "macros", None)
        if macros_mgr:
            for m in macros_mgr.list_macros():
                if m not in commands:
                    commands.append(m)
        return sorted(commands)

    def _get_active_users(self) -> list[str]:
        """Returns the list of active users from the user sidebar."""
        try:
            from ui.user_list import UserListSidebar
            sidebar = self.app.query_one(UserListSidebar)
            return sidebar.get_users()
        except Exception:
            return []

    def action_autocomplete(self) -> None:
        """Autocompletes commands, subcommands, or user names on Tab."""
        # If currently in an active tab completion cycle, cycle to next candidate
        if self._tab_candidates and self._tab_index != -1:
            self._tab_index = (self._tab_index + 1) % len(self._tab_candidates)
            candidate = self._tab_candidates[self._tab_index]
            self.value = f"{self._tab_base}{candidate} "
            self.cursor_position = len(self.value)
            return

        text = self.value

        # 1. Slash command or macro completion (e.g. "/c", "/t", "/")
        if text.startswith("/") and " " not in text:
            prefix = text[1:].lower()
            all_cmds = self._get_available_commands()
            matches = [cmd for cmd in all_cmds if cmd.lower().startswith(prefix)]
            if matches:
                self._tab_base = "/"
                self._tab_candidates = matches
                self._tab_index = 0
                self.value = f"/{matches[0]} "
                self.cursor_position = len(self.value)
            return

        # 2. Subcommand and argument completion
        if text.startswith("/") and " " in text:
            parts = text[1:].split()
            trailing_space = text.endswith(" ")
            cmd_name = parts[0].lower()

            # A. User / Occupant name completion for /users del, /notify watch, /notify unwatch
            if (cmd_name in ("users", "user") and len(parts) >= 2 and parts[1].lower() in ("del", "remove", "leave")) or \
               (cmd_name in ("notify") and len(parts) >= 2 and parts[1].lower() in ("watch", "unwatch", "add", "del")):
                prefix = "" if trailing_space else parts[-1].lower()
                active_users = self._get_active_users()
                matches = [u for u in active_users if u.lower().startswith(prefix)]
                if matches:
                    base_tokens = parts[:-1] if not trailing_space else parts
                    self._tab_base = f"/{' '.join(base_tokens)} "
                    self._tab_candidates = matches
                    self._tab_index = 0
                    self.value = f"{self._tab_base}{matches[0]} "
                    self.cursor_position = len(self.value)
                return

            # B. Subcommands completion (e.g. "/log ", "/macro s")
            if cmd_name in SUBCOMMANDS:
                sub_prefix = "" if trailing_space else parts[1].lower() if len(parts) > 1 else ""
                candidates = SUBCOMMANDS[cmd_name]
                matches = [s for s in candidates if s.lower().startswith(sub_prefix)]
                if matches:
                    self._tab_base = f"/{cmd_name} "
                    self._tab_candidates = matches
                    self._tab_index = 0
                    self.value = f"{self._tab_base}{matches[0]} "
                    self.cursor_position = len(self.value)
                return

        # 3. Direct player mention completion (e.g. "@Ali")
        if "@" in text:
            last_word = text.split()[-1]
            if last_word.startswith("@"):
                prefix = last_word[1:].lower()
                active_users = self._get_active_users()
                matches = [u for u in active_users if u.lower().startswith(prefix)]
                if matches:
                    base = text[: len(text) - len(last_word)]
                    self._tab_base = f"{base}@"
                    self._tab_candidates = matches
                    self._tab_index = 0
                    self.value = f"{self._tab_base}{matches[0]} "
                    self.cursor_position = len(self.value)
                return
