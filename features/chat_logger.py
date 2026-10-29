"""Chat and session logger for MCP client."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from rich.text import Text


class ChatLogger:
    """Manages file-based session and chat logging."""

    def __init__(self, enabled: bool = True, log_dir: str = "logs", level: str = "full"):
        self.enabled = enabled
        self.log_dir = Path(log_dir)
        self.level = level.lower()  # "chat", "system", or "full"
        self._current_file: Path | None = None

        if self.enabled:
            self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensures that the log directory exists."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _get_log_file(self) -> Path:
        """Returns the log file path for the current date."""
        self._ensure_dir()
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"session_{date_str}.log"

    def log(self, text: str, category: str = "chat") -> None:
        """Logs a message if logging is enabled and matches the current level."""
        if not self.enabled or not text:
            return

        cat = category.lower()
        if self.level == "chat" and cat != "chat":
            return
        if self.level == "system" and cat != "system":
            return

        try:
            clean_text = Text.from_markup(str(text)).plain.strip()
        except Exception:
            clean_text = str(text).strip()

        if not clean_text:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{cat.upper()}] {clean_text}\n"

        target_file = self._get_log_file()
        self._current_file = target_file

        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except OSError:
            pass

    def enable(self) -> None:
        """Enables logging."""
        self.enabled = True
        self._ensure_dir()

    def disable(self) -> None:
        """Disables logging."""
        self.enabled = False

    def get_status(self) -> str:
        """Returns a human-readable status string."""
        state = "Enabled" if self.enabled else "Disabled"
        target = self._current_file or self._get_log_file()
        return f"Status: {state} | Level: {self.level} | Directory: {self.log_dir} | Current file: {target.name}"
