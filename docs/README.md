# MCP Client - Terminal AI & Model Context Protocol Client

> ✨ *“A terminal client that feels like a lovechild of a hacker tool, an AI workstation, and a Discord chat — fully local, open-source, and built in pure Python with Textual.”*

A modern, retro-futuristic terminal application for interacting with **AI Model Context Protocol (Anthropic MCP standard)** servers and large language models (LLMs). Connect external tools, filesystem servers, APIs, and databases directly to an intelligent agent with a real-time terminal user interface.

---

## 🌟 Overview: What is MCP?

The **Model Context Protocol (MCP 2024-11-05)** is an open standard introduced by Anthropic that standardizes how AI applications connect to external tools, resources, and contextual data. Instead of hardcoding bespoke API integrations into an agent, MCP allows external programs to run as isolated subprocesses that communicate with the client over JSON-RPC 2.0 (stdio or SSE).

This client serves as both a **standalone MCP server inspector** (allowing manual tool inspection and execution) and an **autonomous AI assistant** (where models such as local Ollama or OpenAI dynamically invoke registered tools to answer your questions).

---

## ✅ Core Features

### 🤖 **1. AI Chat & Autonomous Tool Calling** (`core/llm_agent.py`)
*   **Direct Chat Prompting:** Type natural questions like *"What is 25 * 4 + 10?"* or *"What is my operating system and python version?"* into the input bar. The client formats connected MCP tools into standard function calling schemas and routes queries to the model.
*   **Autonomous Tool Execution:** The LLM decides when to invoke MCP tools, the client runs them locally, and injects the output back into the conversation for a final synthesized response.
*   **Multi-Provider Support:**
    *   **Ollama:** Fully local and private (`http://localhost:11434`, e.g. `llama3.2`, `qwen2.5`, `mistral`) with zero API keys required.
    *   **OpenAI:** Standard `/v1/chat/completions` API endpoints.
    *   **Mock Demo Agent:** Built-in offline agent for immediate testing without external dependencies.
*   **Direct AI Commands:** Dedicated `/ai <prompt>` and `/ask <prompt>` commands, plus live inspection and configuration via `/llm`.

### 🔌 **2. MCP Multi-Server Engine** (`core/mcp_client.py`, `core/server_manager.py`)
*   **JSON-RPC 2.0 Stdio Subprocess Transport:** Manages concurrent background server processes adhering strictly to the MCP 2024-11-05 standard.
*   **Automated Lifecycle & Handshake:** Performs protocol negotiation (`initialize` & `notifications/initialized`) and refreshes capabilities (`tools/list`, `resources/list`, `prompts/list`).
*   **Multi-Server Routing:** Aggregates tools across all active servers and routes calls to the appropriate process.
*   **Claude Desktop Compatibility:** Configured in `config/settings.yaml` using the familiar `mcpServers` JSON/YAML schema.

### 📦 **3. Built-in Sample MCP Server** (`assets/sample_server.py`)
*   Included out of the box to test Model Context Protocol without external setup:
    *   `echo`: Echoes back user messages.
    *   `system_info`: Inspects platform architecture, OS, Python version, and system time.
    *   `math_eval`: Safe mathematical AST evaluator for arithmetic calculations.
    *   Sample resource (`memo://welcome`) and prompt template (`system_check`).

### 🖥️ **4. Terminal UI & Explorer Sidebar** (`ui/server_sidebar.py`, `ui/interface.py`)
*   **MCP Explorer Sidebar (`F2` / `Ctrl+B` / `/sidebar`):**
    *   Live server status badges (`● sample [CONNECTED]`, `● [CONNECTING]`, `○ [STOPPED]`, `● [ERROR]`).
    *   Expandable list of available tools with descriptions, server resources, and prompts.
    *   Flicker-free reactive updates synchronized with the status loop.
*   **Scrollback Search Drawer (`Ctrl+F` / `F4` / `/search`):** Collapsible drawer to search message history with live match highlighting.
*   **Telemetry Status Bar (`F3`):** Bottom status bar displaying server count, connection health, logging status, active timers, and clock.

### ⚡ **5. Context-Aware Tab Autocompletion** (`ui/input_handler.py`)
*   **Top-Level Commands:** Autocompletes `/servers`, `/tools`, `/call`, `/sidebar`, `/ai`, `/llm`, and standard commands.
*   **Subcommands:** Autocompletes `/servers start`, `/servers stop`, `/sidebar toggle`, etc.
*   **Dynamic Tool Names:** Tab after `/call ` or `/tools ` autocompletes available tool names (`echo`, `math_eval`, `system_info`) and cycles through candidates.
*   **Dynamic Server Names:** Tab after `/servers start ` or `/servers stop ` autocompletes registered server instances.

---

## ⌨️ Keybindings Quick Reference

| Key | Action |
|---|---|
| **Tab** | Context-aware autocompletion (commands, subcommands, tools, servers; press again to cycle) |
| **Up / Down** | Cycle through input command/message history |
| **F2** / **Ctrl + B** | Toggle MCP Server & Tool Explorer Sidebar |
| **F3** | Toggle bottom telemetry status bar |
| **Ctrl + F** / **F4** | Open / Close interactive scrollback search bar |
| **Esc** | Close search bar or clear the current input line |

---

## 💻 Available Slash Commands

### **MCP Server & Tool Commands**
| Command | Usage | Description |
|---|---|---|
| `/servers` | `/servers [list\|start <n>\|stop <n>\|add <n> <cmd> [args...]\|toggle]` | Manage, monitor, start, or register MCP servers |
| `/tools` | `/tools [tool_name]` | List available MCP tools across all connected servers or view JSON schema |
| `/call` | `/call <tool_name> [json_arguments]` | Manually invoke an MCP tool with JSON arguments |
| `/sidebar` | `/sidebar [toggle\|refresh]` | Toggle or force-reload the MCP Explorer sidebar (alias: `/explorer`) |

### **AI Assistant & LLM Commands**
| Command | Usage | Description |
|---|---|---|
| `/ai` | `/ai <prompt>` | Prompt the AI assistant to answer a query or invoke MCP tools (alias: `/ask`) |
| `/llm` | `/llm [status\|toggle\|provider <p>\|model <m>\|clear]` | View status, toggle AI chat, switch provider (`ollama`, `openai`, `mock`), or set model |

### **General & Utility Commands**
| Command | Usage | Description |
|---|---|---|
| `/search` | `/search <query>` | Search scrollback history for matching messages (alias: `/find`) |
| `/status` | `/status [bar [toggle\|on\|off]]` | Show diagnostic telemetry report or toggle status bar widget |
| `/macro` | `/macro [list\|set <n> <tmpl>\|del <n>]` | Manage custom command macros (`$1`, `$*`, chained `;`) |
| `/log` | `/log [status\|on\|off]` | View or toggle session file logging (`logs/session_YYYY-MM-DD.log`) |
| `/notify` | `/notify [status\|on\|off\|sound\|watch <w>\|unwatch <w>\|list\|test]` | Manage audio/toast notifications and keyword alerts |
| `/trigger` | `/trigger [list\|add <pat> => <act>\|toggle <id>\|del <id>]` | Event-driven regex automation triggers |
| `/ticker` | `/ticker [list\|add <sec> <cmd>\|del <id>]` | Manage periodic timed background tasks |
| `/clear` | `/clear` | Clear the chat display (preserves scrollback search history) |
| `/help` | `/help` | Display list of available commands |
| `/quit` | `/quit` | Gracefully shut down and exit the client |

---

## ⚙️ Configuration (`config/settings.yaml`)

Edit `config/settings.yaml` to register your MCP servers and configure your LLM provider:

```yaml
# MCP Servers (Anthropic Model Context Protocol standard)
mcpServers:
  # Built-in local Python sample server
  sample:
    command: "python3"
    args: ["-u", "assets/sample_server.py"]

  # Example: Official Filesystem MCP server via npx
  # filesystem:
  #   command: "npx"
  #   args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]

# LLM AI Assistant & Autonomous Tool-Calling
llm:
  enabled: true
  provider: "ollama"       # Options: 'ollama' (local), 'openai' (API), or 'mock' (built-in demo)
  base_url: "http://localhost:11434"
  model: "llama3.2"        # Model to use in Ollama or OpenAI
  api_key: ""              # Optional API key for OpenAI-compatible endpoints
  temperature: 0.7

ui:
  theme: "default"
  show_user_list: true     # Starts with MCP Explorer sidebar visible
  show_status_bar: true

logging:
  enabled: true
  path: "logs"
  level: "full"
```

---

## 🚀 Getting Started

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the Client:**
   ```bash
   python3 main.py
   ```

3. **Start Interacting:**
   - The sample MCP server will connect automatically on startup.
   - Type `/tools` to see available tools.
   - Try manual execution: `/call math_eval {"expression": "25 * 4 + 10"}`
   - Or chat directly: `"What is 25 * 4 + 10?"` and watch the AI agent autonomously execute the tool!
