"""Notification manager for alerts, mentions, and highlights in the MCP client."""

from __future__ import annotations
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App


class NotificationManager:
    """Manages visual toasts, sounds, and keyword mention alerts."""

    def __init__(
        self,
        app: App | None = None,
        enabled: bool = True,
        sound: bool = False,
        initial_keywords: list[str] | None = None,
    ):
        self.app = app
        self.enabled = enabled
        self.sound = sound
        self._keywords: set[str] = set()

        if initial_keywords:
            for kw in initial_keywords:
                self.add_keyword(kw)

    def add_keyword(self, word: str) -> bool:
        """Adds a keyword to monitor."""
        cleaned = word.strip().lower()
        if not cleaned:
            return False
        if cleaned in self._keywords:
            return False
        self._keywords.add(cleaned)
        return True

    def remove_keyword(self, word: str) -> bool:
        """Removes a keyword from monitoring."""
        cleaned = word.strip().lower()
        if cleaned in self._keywords:
            self._keywords.remove(cleaned)
            return True
        return False

    def list_keywords(self) -> list[str]:
        """Returns sorted list of watched keywords."""
        return sorted(self._keywords)

    def notify(
        self,
        message: str,
        title: str = "MCP Alert",
        severity: str = "information",
    ) -> None:
        """Sends a notification toast and optional bell sound."""
        if not self.enabled:
            return

        if self.sound:
            try:
                sys.stdout.write("\a")
                sys.stdout.flush()
            except Exception:
                pass

        if self.app and hasattr(self.app, "notify"):
            try:
                self.app.notify(message, title=title, severity=severity)
            except Exception:
                pass

    def check_incoming(self, text: str) -> str | None:
        """
        Scans incoming text for registered keywords.
        Returns the matched keyword if found and triggers notification.
        """
        if not self.enabled or not self._keywords or not text:
            return None

        lower_text = text.lower()
        for kw in self._keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, lower_text):
                self.notify(
                    f"Mention detected: '{kw}'",
                    title="Keyword Alert",
                    severity="warning",
                )
                return kw

        return None

    def get_status(self) -> str:
        """Returns human-readable status."""
        state = "Enabled" if self.enabled else "Disabled"
        sound_state = "On" if self.sound else "Off"
        count = len(self._keywords)
        return f"Status: {state} | Sound: {sound_state} | Watched keywords: {count}"
