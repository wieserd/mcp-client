"""Input handling and history support for the MCP terminal client."""

from __future__ import annotations
from textual.binding import Binding
from textual.widgets import Input


class HistoryInput(Input):
    """An Input widget that supports cycling through command history with Up/Down keys."""

    BINDINGS = [
        Binding("up", "history_up", "Previous command", show=False),
        Binding("down", "history_down", "Next command", show=False),
        Binding("escape", "clear_input", "Clear input", show=False),
    ]

    def __init__(self, *args, max_history: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.history: list[str] = []
        self.history_index: int = -1
        self._draft: str = ""
        self.max_history = max_history

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

    def action_history_up(self) -> None:
        """Cycle backwards to an older command."""
        if not self.history:
            return

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

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.value = self.history[self.history_index]
        else:
            self.history_index = -1
            self.value = self._draft

        self.cursor_position = len(self.value)

    def action_clear_input(self) -> None:
        """Clears the input bar and resets the history index."""
        self.value = ""
        self.history_index = -1
        self._draft = ""
