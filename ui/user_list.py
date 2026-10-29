"""Backward-compatible user/server sidebar module."""

from __future__ import annotations
from ui.server_sidebar import ServerToolsSidebar


class UserListSidebar(ServerToolsSidebar):
    """Backward compatibility alias for ServerToolsSidebar."""

    def add_user(self, name: str) -> bool:
        return True

    def remove_user(self, name: str) -> bool:
        return True

    def set_users(self, names: list[str]) -> None:
        pass

    def clear_users(self) -> None:
        pass

