# MCP Client - Retro-Futuristic Edition

> ✨ *“A terminal client that feels like a lovechild of a hacker tool, an RPG, and a Discord chat — but fully local, open-source, and built in pure Python.”*

This is a terminal-based MCP (MUD Client Protocol 2.1) client with a focus on modern UX, a polished terminal aesthetic, and quality-of-life features for MUD/MOO players.

---

## ✅ Implemented Functionalities

### **Core Infrastructure & Configuration**
*   **Modular Architecture:** Clean separation of concerns across `config/`, `core/`, `ui/`, and `features/`.
*   **Typed Dataclass Configuration:** Centralized in `config/loader.py` with `AppConfig`, `ServerConfig`, `UIConfig`, and `LoggingConfig`.
*   **Resilient Fallbacks:** Graceful handling of missing or corrupted `settings.yaml` with safe default fallbacks and type validation.
*   **Decoupled Output Architecture:** Centralized `OutputRenderer` in `ui/output_renderer.py` for standardized styling, semantic logging, and decoupling network/parser code from UI widgets.

### **Networking & MCP 2.1 Protocol**
*   **Async TCP Engine:** Asynchronous connection manager in `core/connection.py` utilizing Python's `asyncio`.
*   **Automatic Reconnection & Failover:** Automatically reconnects upon unexpected network dropouts with configurable attempts and delays from `settings.yaml`.
*   **MCP 2.1 Protocol Parser:** Full message parser in `core/mcp_parser.py` supporting:
    *   Header parsing with authentication keys and quoted key-value attributes (`key: "value"`).
    *   Multi-line data packets (`#$#* <tag>` continuation and `#$#: <tag>` termination).
    *   Automated handshake negotiation replying to server capability broadcasts (`mcp`, `mcp-negotiate-can`, `mcp-negotiate-end`).
    *   Extensible package registration via `register_handler(command, callback)`.

### **Modern Terminal UI (Textual)**
*   **Theme & Aesthetic:** Polished dark retro-futuristic theme in `assets/themes/default.css`.
*   **Split Layout & Room Occupant Sidebar:**
    *   Right-side collapsible `UserListSidebar` (`ui/user_list.py`) displaying online users and occupants with status indicators.
    *   Toggled via `F2` / `Ctrl+B` or `/users toggle`.
*   **Detailed Real-time Status Bar:**
    *   `StatusBar` widget (`ui/status_bar.py`) providing live telemetry: connection status, current host/port, logger status, notification alerts, trigger/ticker counts, and a real-time digital clock.
    *   Toggled via `F3` or `/status bar toggle`.
*   **Interactive Scrollback Search Drawer:**
    *   Collapsible `SearchBox` (`ui/search_box.py`) triggered by `Ctrl+F` or `F4`.
    *   Searches past messages with instant match count and timestamped results.
    *   `Esc` dismisses the search drawer and returns focus to the input bar.
*   **Smart History & Autocompletion Input:**
    *   `HistoryInput` (`ui/input_handler.py`) with 100-command circular history (Up/Down arrow navigation).
    *   Interactive **Tab** completion for slash commands, subcommands, custom macros, and active room occupants (with candidate cycling).
    *   `Esc` clears the current input bar.

### **Player Quality-of-Life Features**
*   **Macro System (`features/macros.py`):**
    *   Custom aliases and shortcuts supporting positional parameters (`$1`, `$2`), all-arguments replacement (`$*`), and chained commands (`cmd1; cmd2`).
    *   Managed dynamically via `/macro`.
*   **Automation Engine (`features/scripting.py`):**
    *   **Triggers:** Event-driven regex matching on incoming server text with capture group substitution (`$1`, `$2`, `$0`) to execute automated responses.
    *   **Tickers:** Repeating timers executing commands periodically at custom intervals.
*   **Session Logger (`features/chat_logger.py`):**
    *   Rolling daily log files (`logs/session_YYYY-MM-DD.log`).
    *   Filters by level (`chat`, `system`, or `full`) and strips ANSI/Rich markup to ensure clean plain-text logs.
*   **Notifications & Alerts (`features/notifications.py`):**
    *   Desktop toast notifications via Textual's native alert system.
    *   Audible terminal bell sounds (`\a`).
    *   Word-boundary mention detection on watched keywords or character names.

---

## ⌨️ Keybindings Quick Reference

| Key | Action |
|---|---|
| **Tab** | Autocomplete command, subcommand, macro, or player name (press again to cycle) |
| **Up / Down** | Navigate through previous command/message history |
| **Ctrl + F** / **F4** | Open / Close interactive scrollback search bar |
| **F2** / **Ctrl + B** | Toggle User / Room Occupant Sidebar |
| **F3** | Toggle bottom status bar |
| **Esc** | Close search bar or clear the current input line |

---

## 💻 Available Slash Commands

| Command | Usage | Description |
|---|---|---|
| `/connect` | `/connect [host] [port]` | Connect to the server specified in configuration or arguments |
| `/disconnect` | `/disconnect` | Disconnect gracefully and cancel any auto-reconnection |
| `/reconnect` | `/reconnect` | Instantly reconnect to the last connected server |
| `/help` | `/help` | Display list of available commands |
| `/clear` | `/clear` | Clear the chat display (preserves scrollback search history) |
| `/search` | `/search <query>` | Search scrollback history for matching messages (alias: `/find`) |
| `/status` | `/status [bar [toggle\|on\|off]]` | Show diagnostic system report or toggle status bar widget |
| `/users` | `/users [list\|toggle\|add <n>\|del <n>\|clear]` | Manage or toggle room occupant sidebar |
| `/macro` | `/macro [list\|set <n> <tmpl>\|del <n>]` | Manage custom command macros and aliases |
| `/log` | `/log [status\|on\|off]` | View or toggle session file logging |
| `/notify` | `/notify [status\|on\|off\|sound\|watch <w>\|unwatch <w>\|list\|test]` | Manage audio/toast notifications and keyword alerts |
| `/trigger` | `/trigger [list\|add <pat> => <act>\|toggle <id>\|del <id>]` | Manage event-driven regex triggers |
| `/ticker` | `/ticker [list\|add <sec> <cmd>\|del <id>]` | Manage periodic timed background tasks |
| `/quit` | `/quit` | Gracefully shut down and exit the client |

---

## 🚀 Extended Future Roadmap

The core infrastructure and planned features from the initial roadmap are complete. Future planned extensions include:

*   **Multi-Server Support:** Tabbed interface for concurrent connections to multiple MUD worlds.
*   **Theming Engine:** Live switching between retro themes (Cyberpunk, Amber CRT, Matrix Green, Classic).
*   **Hot-Reloadable Configuration:** `/config reload` to reload `settings.yaml` on the fly.
*   **Mouse Interaction:** Clickable URLs and clickable player names in chat to send tells or open context menus.
