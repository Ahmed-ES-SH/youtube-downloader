import json
from pathlib import Path

from pydantic import BaseModel

CONFIG_PATH = Path.home() / ".ytdl" / "config.json"


class AppConfig(BaseModel):
    default_output_path: str = str(Path.home() / "Downloads" / "ytdl")
    default_format: str = "video"
    default_quality: str = "best"
    default_audio_bitrate: str = "192"
    remember_last: bool = True


def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
        return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2))
