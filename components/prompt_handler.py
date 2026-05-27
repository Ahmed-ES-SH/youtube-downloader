from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from components.config_handler import AppConfig


def get_download_options(config: AppConfig, use_defaults: bool = False) -> dict:
    if use_defaults:
        return {
            "format": config.default_format,
            "quality": config.default_quality,
            "audio_bitrate": config.default_audio_bitrate,
            "output": config.default_output_path,
        }

    fmt = inquirer.select(
        message="Select download format:",
        choices=[
            Choice("video", "Video (MP4)"),
            Choice("audio", "Audio only (MP3)"),
        ],
        default=config.default_format,
    ).execute()

    audio_bitrate = None

    if fmt == "video":
        quality_choices = [
            Choice("best", "Best available"),
            Choice("1080p", "1080p"),
            Choice("720p", "720p"),
            Choice("480p", "480p"),
            Choice("360p", "360p"),
        ]
        quality = inquirer.select(
            message="Select quality:",
            choices=quality_choices,
            default=config.default_quality,
        ).execute()
    else:
        quality = "best"
        audio_bitrate = inquirer.select(
            message="Select audio bitrate:",
            choices=[
                Choice("320", "320kbps"),
                Choice("192", "192kbps"),
                Choice("128", "128kbps"),
            ],
            default=config.default_audio_bitrate,
        ).execute()

    output_choice = inquirer.select(
        message="Output folder:",
        choices=[
            Choice("default", f"Use default  ({config.default_output_path})"),
            Choice("custom", "Enter custom path"),
        ],
    ).execute()

    if output_choice == "custom":
        output_path = inquirer.text(
            message="Enter full path:",
            validate=lambda p: Path(p).expanduser().exists() or "Path does not exist",
        ).execute()
    else:
        output_path = config.default_output_path

    return {
        "format": fmt,
        "quality": quality,
        "audio_bitrate": audio_bitrate,
        "output": output_path,
    }


def ask_skip_or_abort() -> bool:
    result = inquirer.confirm(
        message="Download failed. Skip and continue?",
        default=True,
    ).execute()
    return result


def confirm_download(count: int, output_path: str) -> bool:
    return inquirer.confirm(
        message=f"Ready to download {count} items to: {output_path}. Confirm and start?",
        default=True,
    ).execute()


def select_playlist_items(entries: list[dict]) -> list[dict]:
    choices = []
    for i, entry in enumerate(entries):
        title = entry.get("title", "Unknown")
        choices.append(Choice(value=entry, name=f"{i+1}. {title}", enabled=True))

    selected = inquirer.checkbox(
        message="Select videos to download (space to toggle, enter to confirm):",
        choices=choices,
        cycle=False,
    ).execute()

    return selected if selected else entries
