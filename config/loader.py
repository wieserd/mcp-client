"""Configuration loader and schema definitions for the MCP client."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass
class ServerConfig:
    """Server connection configuration."""
    host: str = "localhost"
    port: int = 6667
    reconnect_attempts: int = 3
    reconnect_delay: int = 5

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class UIConfig:
    """User interface configuration."""
    theme: str = "default"
    show_user_list: bool = True
    show_status_bar: bool = True

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class LoggingConfig:
    """Chat and session logging configuration."""
    enabled: bool = True
    path: str = "logs"
    level: str = "full"

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class MCPServerDefinition:
    """Configuration definition for an AI Model Context Protocol server."""
    command: str = "python3"
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class AppConfig:
    """Root configuration model for the application."""
    server: ServerConfig = field(default_factory=ServerConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    macros: dict[str, str] = field(default_factory=dict)
    mcp_servers: dict[str, MCPServerDefinition] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


def load_config(config_path: Path | str | None = None) -> AppConfig:
    """Loads application configuration from settings.yaml or falls back to defaults."""
    if config_path is None:
        target_path = Path(__file__).parent / "settings.yaml"
    else:
        target_path = Path(config_path)

    raw_data: dict[str, Any] = {}
    if target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    raw_data = loaded
                else:
                    print(f"Warning: {target_path} is not a valid dictionary mapping. Using defaults.")
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing {target_path}: {e}. Using defaults.")
        except OSError as e:
            print(f"Warning: Error reading {target_path}: {e}. Using defaults.")

    server_raw = raw_data.get("server") or {}
    ui_raw = raw_data.get("ui") or {}
    logging_raw = raw_data.get("logging") or {}
    macros_raw = raw_data.get("macros") or {}

    try:
        port = int(server_raw.get("port", 6667))
    except (ValueError, TypeError):
        port = 6667

    try:
        reconnect_attempts = int(server_raw.get("reconnect_attempts", 3))
    except (ValueError, TypeError):
        reconnect_attempts = 3

    try:
        reconnect_delay = int(server_raw.get("reconnect_delay", 5))
    except (ValueError, TypeError):
        reconnect_delay = 5

    server = ServerConfig(
        host=str(server_raw.get("host", "localhost")),
        port=port,
        reconnect_attempts=reconnect_attempts,
        reconnect_delay=reconnect_delay,
    )

    ui = UIConfig(
        theme=str(ui_raw.get("theme", "default")),
        show_user_list=bool(ui_raw.get("show_user_list", True)),
        show_status_bar=bool(ui_raw.get("show_status_bar", True)),
    )

    logging_cfg = LoggingConfig(
        enabled=bool(logging_raw.get("enabled", True)),
        path=str(logging_raw.get("path", "logs")),
        level=str(logging_raw.get("level", "full")),
    )

    macros = {str(k): str(v) for k, v in macros_raw.items()} if isinstance(macros_raw, dict) else {}

    return AppConfig(
        server=server,
        ui=ui,
        logging=logging_cfg,
        macros=macros,
    )
