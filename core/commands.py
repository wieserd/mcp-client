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

    try:
        await app.connection.connect(host, port)
    except Exception:
        pass

async def command_disconnect(app: App, args: list[str]):
    """Disconnects from the server."""
    renderer = getattr(app, "renderer", None)
    is_active = app.connection.connected or (
        app.connection._reconnect_task and not app.connection._reconnect_task.done()
    )
    if is_active:
        await app.connection.disconnect(manual=True)
    else:
        if renderer:
            renderer.write_warning("Not currently connected.")
        else:
            app.query_one("#chat_window").write("[yellow]Not currently connected.[/]")

async def command_reconnect(app: App, args: list[str]):
    """Reconnects to the last connected server (Usage: /reconnect)."""
    host = app.connection._last_host
    port = app.connection._last_port

    if not host or not port:
        server_config = getattr(app.config, "server", None) or (app.config.get("server", {}) if isinstance(app.config, dict) else {})
        host = getattr(server_config, "host", "localhost") if hasattr(server_config, "host") else server_config.get("host", "localhost")
        port = getattr(server_config, "port", 6667) if hasattr(server_config, "port") else server_config.get("port", 6667)

    if app.connection.connected:
        await app.connection.disconnect(manual=True)

    try:
        await app.connection.connect(host, port)
    except Exception:
        pass

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

async def command_notify(app: App, args: list[str]):
    """Manages notifications and keyword alerts (Usage: /notify [on|off|sound|watch <word>|unwatch <word>|list|test])."""
    renderer = getattr(app, "renderer", None)
    mgr = getattr(app, "notifications", None)

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

    if not mgr:
        write_out("Notification manager is not available.", "error")
        return

    subcmd = args[0].lower() if args else "status"

    if subcmd == "on":
        mgr.enabled = True
        write_out("Notifications enabled.", "success")
    elif subcmd == "off":
        mgr.enabled = False
        write_out("Notifications disabled.", "warning")
    elif subcmd == "sound":
        mode = args[1].lower() if len(args) > 1 else ("off" if mgr.sound else "on")
        mgr.sound = (mode == "on")
        write_out(f"Notification sound set to: {'ON' if mgr.sound else 'OFF'}", "success")
    elif subcmd in ("watch", "add"):
        if len(args) < 2:
            write_out("Usage: /notify watch <keyword>", "error")
            return
        kw = args[1]
        if mgr.add_keyword(kw):
            write_out(f"Now watching keyword: [bold cyan]{kw}[/]", "success")
        else:
            write_out(f"Keyword [bold cyan]{kw}[/] is already being watched.", "warning")
    elif subcmd in ("unwatch", "del", "remove"):
        if len(args) < 2:
            write_out("Usage: /notify unwatch <keyword>", "error")
            return
        kw = args[1]
        if mgr.remove_keyword(kw):
            write_out(f"Removed watched keyword: [bold cyan]{kw}[/]", "success")
        else:
            write_out(f"Keyword [bold cyan]{kw}[/] was not watched.", "warning")
    elif subcmd == "list":
        kws = mgr.list_keywords()
        if not kws:
            write_out("No keywords currently watched.", "warning")
        else:
            write_out(f"Watched keywords: [bold cyan]{', '.join(kws)}[/]")
    elif subcmd == "test":
        test_msg = " ".join(args[1:]) if len(args) > 1 else "This is a test notification."
        mgr.notify(test_msg, title="Test Notification")
        write_out("Sent test notification.", "info")
    elif subcmd in ("status", "info"):
        write_out(f"Notifications: {mgr.get_status()}")
    else:
        write_out(f"Unknown option '{subcmd}'. Usage: /notify [on|off|sound|watch <word>|unwatch <word>|list|test]", "error")

async def command_trigger(app: App, args: list[str]):
    """Manages event-driven triggers (Usage: /trigger [list|add <pattern> => <action>|del <id>|toggle <id>])."""
    renderer = getattr(app, "renderer", None)
    scripts = getattr(app, "scripts", None)

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

    if not scripts:
        write_out("Script engine not available.", "error")
        return

    subcmd = args[0].lower() if args else "list"

    if subcmd in ("list", "show"):
        triggers = scripts.list_triggers()
        if not triggers:
            write_out("No triggers registered.", "warning")
            return
        write_out("[bold cyan]Active Triggers:[/]")
        for t in triggers:
            status = "[green]ON[/]" if t.enabled else "[red]OFF[/]"
            write_out(f"  #{t.id} [{status}] [yellow]{t.pattern}[/] => [white]{t.action}[/]")

    elif subcmd in ("add", "new"):
        full_def = " ".join(args[1:])
        if "=>" not in full_def:
            write_out("Usage: /trigger add <pattern> => <action>", "error")
            return
        pattern_str, action_str = full_def.split("=>", 1)
        pattern_str = pattern_str.strip()
        action_str = action_str.strip()
        if not pattern_str or not action_str:
            write_out("Both pattern and action must be specified.", "error")
            return
        try:
            tid = scripts.add_trigger(pattern_str, action_str)
            write_out(f"Trigger #{tid} created: [yellow]{pattern_str}[/] => [white]{action_str}[/]", "success")
        except Exception as e:
            write_out(f"Invalid regular expression: {e}", "error")

    elif subcmd in ("del", "delete", "remove"):
        if len(args) < 2 or not args[1].isdigit():
            write_out("Usage: /trigger del <id>", "error")
            return
        tid = int(args[1])
        if scripts.remove_trigger(tid):
            write_out(f"Trigger #{tid} deleted.", "success")
        else:
            write_out(f"Trigger #{tid} not found.", "warning")

    elif subcmd in ("toggle", "enable", "disable"):
        if len(args) < 2 or not args[1].isdigit():
            write_out("Usage: /trigger toggle <id>", "error")
            return
        tid = int(args[1])
        state = scripts.toggle_trigger(tid)
        if state is not None:
            write_out(f"Trigger #{tid} is now {'ENABLED' if state else 'DISABLED'}.", "success")
        else:
            write_out(f"Trigger #{tid} not found.", "warning")

    else:
        write_out(f"Unknown /trigger command: '{subcmd}'. Usage: /trigger [list|add <pattern> => <action>|del <id>|toggle <id>]", "error")

async def command_ticker(app: App, args: list[str]):
    """Manages repeating timed tasks (Usage: /ticker [list|add <seconds> <command>|del <id>])."""
    renderer = getattr(app, "renderer", None)
    scripts = getattr(app, "scripts", None)

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

    if not scripts:
        write_out("Script engine not available.", "error")
        return

    subcmd = args[0].lower() if args else "list"

    if subcmd in ("list", "show"):
        tickers = scripts.list_tickers()
        if not tickers:
            write_out("No tickers currently running.", "warning")
            return
        write_out("[bold cyan]Active Tickers:[/]")
        for t in tickers:
            write_out(f"  #{t.id} [yellow]Every {t.interval}s[/] => [white]{t.command}[/]")

    elif subcmd in ("add", "start"):
        if len(args) < 3:
            write_out("Usage: /ticker add <seconds> <command>", "error")
            return
        try:
            interval = float(args[1])
            if interval <= 0:
                raise ValueError
        except ValueError:
            write_out(f"Invalid interval: '{args[1]}'. Must be a positive number of seconds.", "error")
            return
        command = " ".join(args[2:])
        tid = scripts.add_ticker(interval, command)
        write_out(f"Ticker #{tid} started (every {interval}s): [white]{command}[/]", "success")

    elif subcmd in ("del", "stop", "remove"):
        if len(args) < 2 or not args[1].isdigit():
            write_out("Usage: /ticker del <id>", "error")
            return
        tid = int(args[1])
        if scripts.remove_ticker(tid):
            write_out(f"Ticker #{tid} stopped.", "success")
        else:
            write_out(f"Ticker #{tid} not found.", "warning")

    else:
        write_out(f"Unknown /ticker command: '{subcmd}'. Usage: /ticker [list|add <seconds> <command>|del <id>]", "error")

async def command_users(app: App, args: list[str]):
    """Manages the online user and room occupant sidebar (Usage: /users [list|toggle|add <name>|del <name>|clear])."""
    renderer = getattr(app, "renderer", None)

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

    sidebar = None
    try:
        from ui.user_list import UserListSidebar
        sidebar = app.query_one(UserListSidebar)
    except Exception:
        pass

    subcmd = args[0].lower() if args else "list"

    if subcmd in ("toggle", "hide", "show"):
        if sidebar:
            visible = sidebar.toggle()
            state = "shown" if visible else "hidden"
            write_out(f"User sidebar is now [bold cyan]{state}[/].", "success")
        else:
            write_out("User sidebar is not available.", "warning")

    elif subcmd in ("list", "who"):
        users = sidebar.get_users() if sidebar else []
        if not users:
            write_out("No users currently registered in room/user list.", "warning")
        else:
            write_out(f"Users online ({len(users)}): [bold cyan]{', '.join(users)}[/]")

    elif subcmd in ("add", "join"):
        if len(args) < 2:
            write_out("Usage: /users add <name>", "error")
            return
        name = " ".join(args[1:])
        if sidebar and sidebar.add_user(name):
            write_out(f"Added [bold cyan]{name}[/] to user list.", "success")
        else:
            write_out(f"User [bold cyan]{name}[/] is already in list or sidebar unavailable.", "warning")

    elif subcmd in ("del", "remove", "leave"):
        if len(args) < 2:
            write_out("Usage: /users del <name>", "error")
            return
        name = " ".join(args[1:])
        if sidebar and sidebar.remove_user(name):
            write_out(f"Removed [bold cyan]{name}[/] from user list.", "success")
        else:
            write_out(f"User [bold cyan]{name}[/] not found in list.", "warning")

    elif subcmd == "clear":
        if sidebar:
            sidebar.clear_users()
            write_out("Cleared all users from list.", "success")
        else:
            write_out("User sidebar is not available.", "warning")

    else:
        write_out(f"Unknown /users option: '{subcmd}'. Usage: /users [list|toggle|add <name>|del <name>|clear]", "error")

async def command_status(app: App, args: list[str]):
    """Displays comprehensive client telemetry or toggles the status bar (Usage: /status [bar [toggle|on|off]])."""
    renderer = getattr(app, "renderer", None)

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

    # Check for /status bar subcommands
    if args and args[0].lower() == "bar":
        try:
            from ui.status_bar import StatusBar
            bar = app.query_one(StatusBar)
        except Exception:
            bar = None

        if not bar:
            write_out("Status bar widget is not loaded.", "warning")
            return

        action = args[1].lower() if len(args) > 1 else "toggle"
        if action in ("toggle", "switch"):
            visible = bar.toggle()
            write_out(f"Status bar is now {'shown' if visible else 'hidden'}.", "success")
        elif action in ("on", "show"):
            bar.remove_class("hidden")
            write_out("Status bar shown.", "success")
        elif action in ("off", "hide"):
            bar.add_class("hidden")
            write_out("Status bar hidden.", "warning")
        else:
            write_out("Usage: /status bar [toggle|on|off]", "error")
        return

    # Full diagnostic status report
    write_out("[bold cyan]═══ MCP Client Status ═══[/]")

    # 1. Connection
    conn = getattr(app, "connection", None)
    if conn and conn.connected:
        target = f"{conn._last_host}:{conn._last_port}" if conn._last_port else conn._last_host
        write_out(f"  [bold green]● Connection:[/] Connected to [white]{target}[/]")
    elif conn and conn._reconnect_task and not conn._reconnect_task.done():
        write_out("  [bold yellow]● Connection:[/] Reconnecting in background...")
    else:
        write_out("  [bold red]● Connection:[/] Disconnected")

    # 2. Logging
    logger = getattr(app, "logger", None)
    if logger and logger.enabled:
        write_out(f"  [cyan]● Logger:[/] Enabled (level: {logger.level}, dir: {logger.log_dir})")
    else:
        write_out("  [dim]● Logger:[/] Disabled")

    # 3. Notifications
    notify = getattr(app, "notifications", None)
    if notify and notify.enabled:
        kws = notify.list_keywords()
        sound_str = " (sound ON)" if notify.sound else " (sound OFF)"
        write_out(f"  [magenta]● Notifications:[/] Enabled{sound_str} | Watched: {len(kws)}")
    else:
        write_out("  [dim]● Notifications:[/] Disabled")

    # 4. Macros
    macros = getattr(app, "macros", None)
    macro_count = len(macros.list_macros()) if macros else 0
    write_out(f"  [green]● Macros:[/] {macro_count} registered")

    # 5. Triggers & Tickers
    scripts = getattr(app, "scripts", None)
    if scripts:
        trig_count = len(scripts.list_triggers())
        tick_count = len(scripts.list_tickers())
        write_out(f"  [yellow]● Automation:[/] {trig_count} triggers, {tick_count} active tickers")

    # 6. Users / Occupants
    try:
        from ui.user_list import UserListSidebar
        sidebar = app.query_one(UserListSidebar)
        user_count = len(sidebar.get_users())
    except Exception:
        user_count = 0
    write_out(f"  [blue]● User List:[/] {user_count} occupants active")
    write_out("[bold cyan]═════════════════════════[/]")

async def command_search(app: App, args: list[str]):
    """Searches past scrollback messages (Usage: /search <query> or /find <query>)."""
    renderer = getattr(app, "renderer", None)

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

    if not args:
        write_out("Usage: /search <query> (or press Ctrl+F to open the search bar)", "error")
        return

    query = " ".join(args).strip()
    if not renderer:
        write_out("Renderer not available.", "error")
        return

    results = renderer.search_history(query)
    if not results:
        write_out(f"Search: No matches found for '{query}'.", "warning")
    else:
        write_out(f"[bold cyan]Search results for '[yellow]{query}[/]' ({len(results)} matches):[/]")
        for entry in results:
            time_str = entry.timestamp.strftime("%H:%M:%S")
            escaped_text = entry.text.replace("[", "\\[")
            write_out(f"  [dim]({time_str})[/dim] {escaped_text}")

async def command_clear(app: App, args: list[str]):
    """Clears the chat log window display (Usage: /clear)."""
    renderer = getattr(app, "renderer", None)
    if renderer:
        renderer.clear_display()
    else:
        app.query_one("#chat_window").clear()

# --- Command Registry ---

COMMAND_REGISTRY = {
    "quit": command_quit,
    "help": command_help,
    "connect": command_connect,
    "disconnect": command_disconnect,
    "reconnect": command_reconnect,
    "log": command_log,
    "macro": command_macro,
    "notify": command_notify,
    "trigger": command_trigger,
    "ticker": command_ticker,
    "users": command_users,
    "status": command_status,
    "search": command_search,
    "find": command_search,
    "clear": command_clear,
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
