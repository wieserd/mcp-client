from textual.app import App

# --- Command Functions ---

async def command_quit(app: App, args: list[str]):
    """Stops and exits the application."""
    await app.quit()

async def command_help(app: App, args: list[str]):
    """Displays a list of available commands."""
    chat_log = app.query_one("#chat_window")
    chat_log.write("[bold cyan]Available Commands:[/]")
    for command, func in COMMAND_REGISTRY.items():
        help_text = func.__doc__ or "No description available."
        chat_log.write(f"  [bold green]/{command}[/]: {help_text.strip()}")

async def command_connect(app: App, args: list[str]):
    """Connects to the server specified in the config."""
    if not app.connection.connected:
        host = app.config['server']['host']
        port = app.config['server']['port']
        await app.connection.connect(host, port)
    else:
        app.query_one("#chat_window").write("[yellow]Already connected.[/]")

async def command_disconnect(app: App, args: list[str]):
    """Disconnects from the server."""
    if app.connection.connected:
        await app.connection.disconnect()
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
    chat_log = app.query_one("#chat_window")

    if not user_input.startswith("/"):
        if app.connection.writer and app.connection.connected:
            # Add a newline because servers expect it
            app.connection.writer.write(user_input.encode() + b'\n')
            await app.connection.writer.drain()
            chat_log.write(f"[orange]TO SERVER:[/] {user_input}")
        else:
            chat_log.write("[bold red]Not connected. Use /connect to establish a connection.[/]")
        return

    parts = user_input[1:].split()
    command_name = parts[0].lower()
    args = parts[1:]

    command_func = COMMAND_REGISTRY.get(command_name)

    if command_func:
        await command_func(app, args)
    else:
        chat_log.write(f'[bold red]Unknown command: [white]/{command_name}[/]. Type /help for a list of commands.[/]')
