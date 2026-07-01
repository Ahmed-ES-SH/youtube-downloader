import re
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from components.config_handler import AppConfig


def time_to_seconds(t: str) -> int:
    parts = t.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def validate_time(val: str) -> bool | str:
    if not re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", val):
        return "Use MM:SS or HH:MM:SS format (e.g. 1:30 or 1:00:00)"
    parts = val.split(":")
    if len(parts) == 2:
        m, s = int(parts[0]), int(parts[1])
        if s < 60:
            return True
    else:
        _, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        if m < 60 and s < 60:
            return True
    return "Seconds and minutes must be less than 60"


def ask_trim_settings() -> dict | None:
    if not inquirer.confirm(message="Do you want to cut a section?", default=False).execute():
        return None

    start = inquirer.text(
        message="Start time (MM:SS or HH:MM:SS):",
        validate=validate_time,
    ).execute()

    end = inquirer.text(
        message="End time (MM:SS or HH:MM:SS):",
        validate=validate_time,
    ).execute()

    if time_to_seconds(start) >= time_to_seconds(end):
        print("  Start time must be before end time. Skipping trim.")
        return None

    return {"start_time": start, "end_time": end}


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


def _selection_summary(entries: list[dict], start: int, end: int | None = None):
    end = end or len(entries)
    print(f"  Selected {end - start + 1} video(s):")
    for i, entry in enumerate(entries[start - 1:end], start=start):
        title = entry.get("title", "Unknown")
        max_w = 60
        title_short = title if len(title) <= max_w else title[:max_w - 3] + "..."
        print(f"    {i}. {title_short}")


def confirm_download(count: int, output_path: str, options: dict | None = None) -> bool:
    if options:
        fmt = "MP3" if options.get("format") == "audio" else "MP4"
        quality = options.get("quality", "best")
        audio_bitrate = options.get("audio_bitrate")
        trim = options.get("trim")
        playlist_range = options.get("playlist_range")
        dash = "\u2500"

        print(f"  {dash * 2} Download Summary {dash * 2}")
        print(f"  Format:  {fmt}" + (f" ({quality})" if fmt == "MP4" else "") + (f" ({audio_bitrate}kbps)" if audio_bitrate else ""))
        print(f"  Items:   {count}")
        if playlist_range:
            print(f"  Range:   #{playlist_range['start']} to #{playlist_range['end']} (of {playlist_range['total']})")
        if trim:
            print(f"  Trim:    {trim['start_time']} to {trim['end_time']}")
        print(f"  Output:  {output_path}")
        print(f"  {dash * 20}")

    return inquirer.confirm(
        message="Confirm and start download?",
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


def select_playlist_range(entries: list[dict]) -> list[dict]:
    count = len(entries)
    start_num, end_num = _ask_range_bounds(count)
    selected = entries[start_num - 1:end_num]
    _selection_summary(selected, start_num, end_num)
    return selected


def select_playlist_range_bounds(total: int) -> tuple[int, int]:
    start, end = _ask_range_bounds(total)
    print(f"  Selected items #{start} to #{end} ({end - start + 1} of {total})")
    return (start, end)


def _ask_range_bounds(total: int) -> tuple[int, int]:
    def _parse_range_input(val: str) -> tuple[int, int] | str:
        if "-" in val:
            parts = val.split("-", 1)
            if parts[0].isdigit() and parts[1].isdigit():
                s, e = int(parts[0]), int(parts[1])
                if 1 <= s <= e <= total:
                    return (s, e)
            return f"Use format start-end (e.g. 10-20) within 1-{total}"
        if val.isdigit():
            n = int(val)
            if 1 <= n <= total:
                return (n, total)
            return f"Enter a number between 1 and {total}"
        return f"Enter a number or range (e.g. 10 or 10-20) within 1-{total}"

    def _validator(val: str) -> bool:
        result = _parse_range_input(val)
        return isinstance(result, tuple)

    raw = inquirer.text(
        message=f"Range (1-{total}), e.g. 10-20 or just 10 for 10 to end:",
        validate=_validator,
        invalid_message="Invalid range",
    ).execute()

    result = _parse_range_input(raw)
    return result
