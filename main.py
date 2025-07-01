from config.loader import load_config
from ui.interface import MCPApp

def main():
    """Main entry point for the MCP client."""
    config = load_config()
    if not config:
        print("Could not load configuration. Exiting.")
        return

    app = MCPApp(config=config)
    app.run()

if __name__ == "__main__":
    main()
