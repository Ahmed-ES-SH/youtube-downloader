import re

import yt_dlp

YT_URL_PATTERN = re.compile(
    r"^(https?://)?((www|m|music)\.)?(youtube\.com/(watch\?.*?v=|playlist\?.*?list=|shorts/|live/|embed/)|youtu\.be/)[\w\-]+"
)


def is_valid_youtube_url(url: str) -> bool:
    if not url:
        return False
    return bool(YT_URL_PATTERN.match(url.strip()))


def _is_entry_available(entry: dict | None) -> bool:
    if entry is None:
        return False
    title = (entry.get("title") or "").lower()
    if not entry.get("url") and not entry.get("id"):
        return False
    return not any(
        keyword in title for keyword in ["[private", "[deleted", "[unavailable"]
    )


def detect_url_type(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "ignore_no_formats_error": True,
        "nocheckcertificate": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url.strip(), download=False)

    if not info:
        raise ValueError("Could not retrieve video or playlist information.")

    if info.get("_type") == "playlist":
        entries = info.get("entries", []) or []
        available = [e for e in entries if _is_entry_available(e)]
        for e in available:
            e_url = e.get("url") or ""
            if not e_url.startswith("http"):
                video_id = e.get("id") or e_url
                e["url"] = f"https://www.youtube.com/watch?v={video_id}"
        total = info.get("playlist_count") or len(available)
        return {
            "type": "playlist",
            "title": info.get("title") or "Playlist",
            "count": total,
            "url": url,
            "entries": available,
        }
    return {
        "type": "video",
        "title": info.get("title") or "Video",
        "count": 1,
        "url": url,
        "entries": [info],
    }
