"""Output renderer for formatting and displaying messages in the terminal UI."""

from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
from rich.text import Text

if TYPE_CHECKING:
    from textual.app import App
    from textual.widgets import RichLog


class OutputRenderer:
    """Formats and writes output messages to the chat/log window."""

    def __init__(self, app: App, chat_widget_id: str = "#chat_window"):
        self.app = app
        self.chat_widget_id = chat_widget_id

    def _get_chat_log(self) -> RichLog | None:
        try:
            return self.app.query_one(self.chat_widget_id)
        except Exception:
            return None

    def _log(self, content: str | Text, category: str = "system") -> None:
        logger = getattr(self.app, "logger", None)
        if logger:
            raw = content.plain if isinstance(content, Text) else str(content)
            logger.log(raw, category=category)

    def write(self, content: str | Text, category: str = "system") -> None:
        """Writes arbitrary string markup or Text to the chat window and logs it."""
        log = self._get_chat_log()
        if log is not None:
            if isinstance(content, str):
                log.write(Text.from_markup(content))
            else:
                log.write(content)
        self._log(content, category=category)

    def write_info(self, message: str) -> None:
        """Writes an informational message."""
        self.write(f"[cyan]{message}[/]", category="system")

    def write_success(self, message: str) -> None:
        """Writes a success message."""
        self.write(f"[bold green]{message}[/]", category="system")

    def write_warning(self, message: str) -> None:
        """Writes a warning message."""
        self.write(f"[yellow]{message}[/]", category="system")

    def write_error(self, message: str) -> None:
        """Writes an error message."""
        self.write(f"[bold red]{message}[/]", category="system")

    def write_sent(self, message: str) -> None:
        """Writes an outgoing message sent to the server."""
        self.write(f"[orange3]TO SERVER:[/] {message}", category="chat")

    def write_mcp(self, text: str) -> None:
        """Writes an MCP protocol notification."""
        self.write(f"[bold magenta]MCP:[/] {text}", category="system")

    def write_server(self, text: str) -> None:
        """Writes incoming text from the server."""
        log = self._get_chat_log()
        if log is not None:
            # Server text might have rich markup characters like '['; treat raw server text cleanly
            log.write(Text(text))
        self._log(text, category="chat")

        notifications = getattr(self.app, "notifications", None)
        if notifications:
            notifications.check_incoming(text)

        scripts = getattr(self.app, "scripts", None)
        if scripts:
            triggered_cmds = scripts.evaluate_triggers(text)
            for cmd in triggered_cmds:
                from core.commands import process_command
                asyncio.create_task(process_command(self.app, cmd))
