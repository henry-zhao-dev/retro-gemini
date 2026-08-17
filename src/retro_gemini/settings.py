import json
from dataclasses import dataclass, asdict
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

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Unpack the dictionary into the dataclass arguments
                    return cls(
                        **{k: v for k, v in data.items() if k in cls.__annotations__}
                    )
            except Exception:
                # Fallback if file is corrupted
                pass

        # Return default instance if file doesn't exist or failed to load
        return cls()
