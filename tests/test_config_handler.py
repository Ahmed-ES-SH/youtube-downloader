import json
from unittest.mock import patch

from components.config_handler import AppConfig, load_config, save_config


def test_load_defaults_when_no_file():
    with patch("components.config_handler.CONFIG_PATH") as mock_path:
        mock_path.exists.return_value = False
        config = load_config()
        assert config.default_format == "video"
        assert config.default_quality == "best"


def test_load_from_existing_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "default_format": "audio",
                "default_quality": "720p",
                "default_audio_bitrate": "320",
                "default_output_path": "/tmp/test",
                "remember_last": True,
            }
        )
    )
    with patch("components.config_handler.CONFIG_PATH", config_file):
        config = load_config()
        assert config.default_format == "audio"
        assert config.default_quality == "720p"


def test_save_config(tmp_path):
    config_file = tmp_path / ".ytdl" / "config.json"
    config = AppConfig(default_format="audio", default_quality="1080p")
    with patch("components.config_handler.CONFIG_PATH", config_file):
        save_config(config)
        data = json.loads(config_file.read_text())
        assert data["default_format"] == "audio"
