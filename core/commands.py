from textual.app import App

# --- Command Functions ---

def command_quit(app: App, args: list[str]):
    """Stops and exits the application."""
    app.exit()

def command_help(app: App, args: list[str]):
    """Displays a list of available commands."""
    chat_log = app.query_one("#chat_window")
    chat_log.write("[bold cyan]Available Commands:[/]")
    for command, func in COMMAND_REGISTRY.items():
        # Docstrings are used as the help text
        help_text = func.__doc__ or "No description available."
        chat_log.write(f"  [bold green]/{command}[/]: {help_text.strip()}")

# --- Command Registry ---

COMMAND_REGISTRY = {
    "quit": command_quit,
    "help": command_help,
}

# --- Main Processor ---

def process_command(app: App, user_input: str):
    """Processes user input, distinguishing between local commands and server messages."""
    chat_log = app.query_one("#chat_window")

    if not user_input.startswith("/"):
        # If it's not a command, treat it as a message to be sent to the server.
        chat_log.write(f"[yellow]TO SERVER:[/] {user_input}")
        return

    # It's a command, so we process it.
    parts = user_input[1:].split()
    command_name = parts[0].lower()
    args = parts[1:]

    command_func = COMMAND_REGISTRY.get(command_name)

    if command_func:
        command_func(app, args)
    else:
        chat_log.write(f'[bold red]Unknown command: [white]/{command_name}[/]. Type /help for a list of commands.[/]')