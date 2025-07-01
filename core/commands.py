from textual.app import App

def process_command(app: App, user_input: str):
    """Processes user input, distinguishing between local commands and server messages."""
    chat_log = app.query_one("#chat_window")

    if user_input.startswith("/"):
        command_parts = user_input[1:].split()
        command = command_parts[0].lower()

        if command == "quit":
            app.exit()
            return
        else:
            chat_log.write(f"[bold red]Unknown command: /{command}[/]")
            return

    # If it's not a command, treat it as a message to be sent to the server.
    # For now, we'll just echo it with a "send" prefix.
    chat_log.write(f"[yellow]TO SERVER:[/] {user_input}")
