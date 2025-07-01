# MCP Client - Retro-Futuristic Edition

> ✨ *“A terminal client that feels like a lovechild of a hacker tool, an RPG, and a Discord chat — but fully local, open-source, and built in pure Python.”*

This is a terminal-based MCP (MUD Client Protocol) client with a focus on modern UX, a polished terminal aesthetic, and quality-of-life features for MUD players.

---

## ✅ Implemented Functionalities

This project is in its early stages. Here is what has been implemented so far:

### **Core Infrastructure**
*   **Project Scaffolding:** A clean, modular project structure has been created, separating concerns for configuration, core logic, UI, and features.
*   **Dependency Management:** Uses `requirements.txt` with `textual` for the UI and `pyyaml` for configuration.
*   **Configuration Loading:** The application loads server details and UI settings from `config/settings.yaml`. The loading logic is centralized in `config/loader.py`.

### **Terminal UI (TUI)**
*   **Modern TUI Framework:** Built using the powerful `textual` library.
*   **Polished "Vibe":** A dark, retro-futuristic theme is implemented in `assets/themes/default.css`.
*   **Interactive Layout:**
    *   A cool ASCII art logo in the header.
    *   A scrollable, bordered window for chat/log output (`RichLog`).
    *   An interactive input bar for typing commands and messages.
*   **Basic Interactivity:** The UI is fully interactive. Text entered in the input bar is processed on `Enter`.

### **Command Processing**
*   **Command Dispatcher:** A basic command processor is in place (`core/commands.py`).
*   **Local Command Handling:** The system can distinguish between local commands (prefixed with `/`) and messages intended for the server.
*   **`/quit` Command:** The first local command, `/quit`, has been implemented to gracefully exit the application.

---

## 🚀 Future Improvements

The following features from the original outline are planned for future development:

*   **Network & Protocol Handling:**
    *   Implement the TCP socket connection in `core/connection.py`.
    *   Build the MCP protocol parser in `core/mcp_parser.py`.
    *   Add robust reconnect and failover logic.
*   **Expanded Command System:**
    *   Add more local commands (`/connect`, `/disconnect`, `/help`, `/macro`).
    *   Implement command aliases.
*   **Advanced UI Features:**
    *   Display a user list.
    *   Add a status/info bar.
    *   Implement scrollback search in the chat window.
    *   Add autocompletion for commands and names.
*   **Quality of Life Features:**
    *   **Macros:** Implement the full macro system from `features/macros.py`.
    *   **Scripting:** Build the Python or DSL-based scripting engine.
    *   **Chat Logger:** Create the session logger in `features/chat_logger.py`.
    *   **Notifications:** Add sound and UI alerts for events.
*   **Extended Features:**
    *   Multi-server tabs.
    *   Advanced theming support.
    *   Mouse support for UI interaction.

---

## 🐞 Known Errors & Limitations

*   **No Network Connectivity:** The client does **not** currently connect to any server. All messages typed are simply echoed to the local log for demonstration purposes and are prefixed with `[TO SERVER:]`.
*   **Limited Command Knowledge:** The command processor only recognizes `/quit`. Any other command will result in an "Unknown command" error.
*   **Configuration is Static:** The `settings.yaml` file is loaded at startup, but there is no in-app way to modify or reload the configuration yet.
