"""Loading and saving persistent application settings."""

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from platformdirs import user_config_path

_APP_NAME = "retro-gemini"
_APP_AUTHOR = "henry-zhao-dev"


@dataclass
class AppSettings:
    default_model: str = "gemini-flash-lite-latest"

    @staticmethod
    def get_path() -> Path:
        """Helper to get the OS-appropriate path."""
        config_dir = user_config_path(_APP_NAME, _APP_AUTHOR)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "settings.json"

    def save(self) -> None:
        """Saves the current instance state to disk."""
        config_file = self.get_path()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "AppSettings":
        """
        Loads settings from disk, falling back to default values
        if missing/corrupted.
        """
        config_file = cls.get_path()
        if not config_file.exists():
            return cls()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except OSError, UnicodeError, json.JSONDecodeError:
            return cls()

        if not isinstance(data, dict):
            return cls()

        setting_names = {field.name for field in fields(cls) if field.init}
        saved_settings = {
            key: value for key, value in data.items() if key in setting_names
        }

        try:
            return cls(**saved_settings)
        except TypeError:
            return cls()
