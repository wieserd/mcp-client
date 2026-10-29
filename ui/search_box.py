"""Interactive search box drawer for scrollback text search."""

from __future__ import annotations
from typing import TYPE_CHECKING
from textual.events import Key
from textual.containers import Horizontal
from textual.widgets import Input, Static

if TYPE_CHECKING:
    from textual.app import App


class SearchInput(Input):
    """Input box for search query handling escape key cleanly."""

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            parent = getattr(self, "parent", None)
            if parent and hasattr(parent, "action_close_search"):
                parent.action_close_search()
                event.prevent_default()
                event.stop()


class SearchBox(Horizontal):
    """Collapsible search bar docked above the status bar."""

    DEFAULT_CSS = """
    SearchBox {
        height: 3;
        background: #181824;
        border-top: solid #00aaaa;
        padding: 0 1;
        display: none;
    }
    SearchBox.visible {
        display: block;
    }
    SearchBox SearchInput#search_query_input {
        width: 1fr;
        height: 1;
        border: none;
        background: #101018;
        color: #ffffff;
        padding: 0 1;
    }
    SearchBox Static#search_hint {
        width: auto;
        color: #888888;
        padding-left: 1;
    }
    """

    def compose(self):
        yield SearchInput(placeholder="Search scrollback (Enter to find, Esc to close)...", id="search_query_input")
        yield Static("Esc to close", id="search_hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when user presses Enter in search box."""
        query = event.value.strip()
        if not query:
            return

        renderer = getattr(self.app, "renderer", None)
        if not renderer:
            return

        results = renderer.search_history(query)
        if not results:
            renderer.write_warning(f"Search: No matches found for '{query}'.")
        else:
            renderer.write(f"[bold cyan]Search results for '[yellow]{query}[/]' ({len(results)} matches):[/]")
            for entry in results:
                time_str = entry.timestamp.strftime("%H:%M:%S")
                # Highlight query matches case-insensitively
                escaped_text = entry.text.replace("[", "\\[")
                renderer.write(f"  [dim]({time_str})[/dim] {escaped_text}")

        # Return focus to chat input
        self.action_close_search()

    def action_close_search(self) -> None:
        """Hides the search box and returns focus to the main input bar."""
        self.remove_class("visible")
        try:
            self.app.query_one("#input_bar").focus()
        except Exception:
            pass

    def open_search(self) -> None:
        """Shows the search box and focuses its input."""
        self.add_class("visible")
        try:
            inp = self.query_one("#search_query_input", SearchInput)
            inp.value = ""
            inp.focus()
        except Exception:
            pass

    def toggle(self) -> bool:
        """Toggles the search bar visibility."""
        if self.has_class("visible"):
            self.action_close_search()
            return False
        else:
            self.open_search()
            return True
