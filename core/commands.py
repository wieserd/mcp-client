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

async def command_log(app: App, args: list[str]):
    """Controls session logging (Usage: /log [on|off|status])."""
    renderer = getattr(app, "renderer", None)
    logger = getattr(app, "logger", None)

    if not logger:
        msg = "Logger is not initialized."
        if renderer:
            renderer.write_error(msg)
        else:
            app.query_one("#chat_window").write(f"[bold red]{msg}[/]")
        return

    subcmd = args[0].lower() if args else "status"

    if subcmd == "on":
        logger.enable()
        msg = f"Chat logging enabled ({logger.get_status()})."
        if renderer:
            renderer.write_success(msg)
        else:
            app.query_one("#chat_window").write(f"[bold green]{msg}[/]")
    elif subcmd == "off":
        logger.disable()
        msg = "Chat logging disabled."
        if renderer:
            renderer.write_warning(msg)
        else:
            app.query_one("#chat_window").write(f"[yellow]{msg}[/]")
    elif subcmd in ("status", "info"):
        msg = f"Logging {logger.get_status()}"
        if renderer:
            renderer.write_info(msg)
        else:
            app.query_one("#chat_window").write(f"[cyan]{msg}[/]")
    else:
        msg = f"Unknown /log option: '{subcmd}'. Usage: /log [on|off|status]"
        if renderer:
            renderer.write_error(msg)
        else:
            app.query_one("#chat_window").write(f"[bold red]{msg}[/]")

async def command_macro(app: App, args: list[str]):
    """Manages custom macros (Usage: /macro [list|set <name> <template>|del <name>])."""
    renderer = getattr(app, "renderer", None)
    macros = getattr(app, "macros", None)

    def write_out(msg: str, style: str = "info") -> None:
        if renderer:
            if style == "success":
                renderer.write_success(msg)
            elif style == "warning":
                renderer.write_warning(msg)
            elif style == "error":
                renderer.write_error(msg)
            else:
                renderer.write(msg)
        else:
            app.query_one("#chat_window").write(msg)

    if not macros:
        write_out("Macro manager not available.", "error")
        return

    subcmd = args[0].lower() if args else "list"

    if subcmd in ("list", "show"):
        all_macros = macros.list_macros()
        if not all_macros:
            write_out("No macros currently defined.", "warning")
            return
        write_out("[bold cyan]Defined Macros:[/]")
        for name, template in sorted(all_macros.items()):
            write_out(f"  [bold green]/{name}[/] -> [white]{template}[/]")

    elif subcmd in ("set", "add"):
        if len(args) < 3:
            write_out("Usage: /macro set <name> <expansion template>", "error")
            return
        name = args[1]
        template = " ".join(args[2:])
        macros.set_macro(name, template)
        write_out(f"Macro [bold green]/{name}[/] set to: [white]{template}[/]", "success")

    elif subcmd in ("del", "delete", "remove"):
        if len(args) < 2:
            write_out("Usage: /macro del <name>", "error")
            return
        name = args[1]
        if macros.remove_macro(name):
            write_out(f"Macro [bold green]/{name}[/] removed.", "success")
        else:
            write_out(f"Macro [white]/{name}[/] not found.", "warning")

    else:
        write_out(f"Unknown /macro action: '{subcmd}'. Usage: /macro [list|set <name> <template>|del <name>]", "error")

# --- Command Registry ---

COMMAND_REGISTRY = {
    "quit": command_quit,
    "help": command_help,
    "connect": command_connect,
    "disconnect": command_disconnect,
    "log": command_log,
    "macro": command_macro,
}

# --- Main Processor ---

async def process_command(app: App, user_input: str, depth: int = 0):
    """Processes user input, distinguishing between local commands, macros, and server messages."""
    renderer = getattr(app, "renderer", None)

    if depth > 10:
        if renderer:
            renderer.write_error("Macro recursion limit exceeded.")
        return
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
        # Check if command matches a configured macro
        macro_mgr = getattr(app, "macros", None)
        if macro_mgr and macro_mgr.get_macro(command_name):
            expanded_commands = macro_mgr.expand(command_name, args)
            for cmd in expanded_commands:
                await process_command(app, cmd, depth=depth + 1)
            return

        msg = f"Unknown command: [white]/{command_name}[/]. Type /help for a list of commands."
        if renderer:
            renderer.write_error(msg)
        else:
            app.query_one("#chat_window").write(f"[bold red]{msg}[/]")
