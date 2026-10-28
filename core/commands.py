from textual.app import App

# --- Command Functions ---

async def command_quit(app: App, args: list[str]):
    """Stops and exits the application."""
    await app.quit()

async def command_help(app: App, args: list[str]):
    """Displays a list of available commands."""
    renderer = getattr(app, "renderer", None)
    if renderer:
        renderer.write("[bold cyan]Available Commands:[/]")
        for command, func in COMMAND_REGISTRY.items():
            help_text = func.__doc__ or "No description available."
            renderer.write(f"  [bold green]/{command}[/]: {help_text.strip()}")
    else:
        chat_log = app.query_one("#chat_window")
        chat_log.write("[bold cyan]Available Commands:[/]")
        for command, func in COMMAND_REGISTRY.items():
            help_text = func.__doc__ or "No description available."
            chat_log.write(f"  [bold green]/{command}[/]: {help_text.strip()}")

async def command_connect(app: App, args: list[str]):
    """Connects to the server specified in the config or via /connect [host] [port]."""
    renderer = getattr(app, "renderer", None)
    if app.connection.connected:
        if renderer:
            renderer.write_warning("Already connected.")
        else:
            app.query_one("#chat_window").write("[yellow]Already connected.[/]")
        return

    server_config = (app.config or {}).get("server", {})
    host = server_config.get("host", "localhost")
    port = server_config.get("port", 6667)

    if len(args) >= 1:
        host = args[0]
    if len(args) >= 2:
        try:
            port = int(args[1])
        except ValueError:
            msg = f"Invalid port: [white]{args[1]}[/]. Port must be a number."
            if renderer:
                renderer.write_error(msg)
            else:
                app.query_one("#chat_window").write(f"[bold red]{msg}[/]")
            return

    await app.connection.connect(host, port)

async def command_disconnect(app: App, args: list[str]):
    """Disconnects from the server."""
    renderer = getattr(app, "renderer", None)
    if app.connection.connected:
        await app.connection.disconnect()
    else:
        if renderer:
            renderer.write_warning("Not currently connected.")
        else:
            app.query_one("#chat_window").write("[yellow]Not currently connected.[/]")

# --- Command Registry ---

COMMAND_REGISTRY = {
    "quit": command_quit,
    "help": command_help,
    "connect": command_connect,
    "disconnect": command_disconnect,
}

# --- Main Processor ---

async def process_command(app: App, user_input: str):
    """Processes user input, distinguishing between local commands and server messages."""
    renderer = getattr(app, "renderer", None)
    stripped = user_input.strip()

    if not stripped:
        return

    if not stripped.startswith("/"):
        if app.connection.writer and app.connection.connected:
            # Add a newline because servers expect it
            app.connection.writer.write(stripped.encode() + b'\n')
            await app.connection.writer.drain()
            if renderer:
                renderer.write_sent(stripped)
            else:
                app.query_one("#chat_window").write(f"[orange]TO SERVER:[/] {stripped}")
        else:
            if renderer:
                renderer.write_error("Not connected. Use /connect to establish a connection.")
            else:
                app.query_one("#chat_window").write("[bold red]Not connected. Use /connect to establish a connection.[/]")
        return

    parts = stripped[1:].split()
    if not parts:
        if renderer:
            renderer.write_warning("No command specified. Type [bold cyan]/help[/] for available commands.")
        else:
            app.query_one("#chat_window").write("[yellow]No command specified. Type [bold cyan]/help[/] for available commands.[/]")
        return

    command_name = parts[0].lower()
    args = parts[1:]

    command_func = COMMAND_REGISTRY.get(command_name)

    if command_func:
        await command_func(app, args)
    else:
        msg = f"Unknown command: [white]/{command_name}[/]. Type /help for a list of commands."
        if renderer:
            renderer.write_error(msg)
        else:
            app.query_one("#chat_window").write(f"[bold red]{msg}[/]")
