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

### **Networking**
*   **Async TCP Connection:** The client now features an asynchronous TCP connection manager in `core/connection.py`.
*   **Connection Management:** It can connect to a server, listen for incoming messages, and handle disconnections gracefully.
*   **Send & Receive:** The client can send user-typed messages to the server and display messages received from the server in the main chat window.

### **Terminal UI (TUI)**
*   **Modern TUI Framework:** Built using the powerful `textual` library.
*   **Polished "Vibe":** A dark, retro-futuristic theme is implemented in `assets/themes/default.css`.
*   **Interactive Layout:**
    *   A cool ASCII art logo in the header.
    *   A scrollable, bordered window for chat/log output (`RichLog`).
    *   An interactive input bar for typing commands and messages.
*   **Real-time Status:** The subtitle bar now dynamically updates to show the current connection status (e.g., "Disconnected", "Connecting...", "Connected").

### **Command Processing**
*   **Scalable Command Registry:** The command processor in `core/commands.py` now uses a dictionary-based registry, making it easy to add new commands.
*   **Local & Remote Command Handling:** The system distinguishes between local client commands (prefixed with `/`) and messages to be sent to the server.
*   **Implemented Commands:**
    *   `/connect`: Connects to the server using settings from `config.yaml`.
    *   `/disconnect`: Disconnects from the server.
    *   `/help`: Lists all available commands.
    *   `/quit`: Gracefully disconnects and exits the application.

---

## 🚀 Future Improvements

The following features from the original outline are planned for future development:

*   **Network & Protocol Handling:**
    *   Build the MCP protocol parser in `core/mcp_parser.py` to handle MCP-specific messages.
    *   Add robust automatic reconnect and failover logic.
*   **Expanded Command System:**
    *   Add more local commands (`/macro`, `/log`, `/script`).
    *   Implement command aliases.
*   **Advanced UI Features:**
    *   Display a user list.
    *   Add a more detailed status/info bar.
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

*   **Raw Protocol Handling:** The client currently displays the raw, unparsed data from the server. It does not yet understand the MCP protocol for features like in-band commands or structured data.
*   **No Automatic Reconnect:** If the connection is lost, the user must manually use `/connect` to reconnect.
*   **Configuration is Static:** The `settings.yaml` file is loaded at startup, but there is no in-app way to modify or reload the configuration yet.
