import yaml
from pathlib import Path

def load_config():
    """Loads the user configuration from settings.yaml."""
    config_path = Path(__file__).parent / "settings.yaml"
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # In a real app, we might want to create a default config here.
        # For now, we'll just return an empty dict.
        return {}
    except yaml.YAMLError as e:
        # Handle potential errors in the YAML file.
        print(f"Error parsing config/settings.yaml: {e}")
        return {}
