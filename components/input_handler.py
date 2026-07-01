import re
import yt_dlp

YT_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|playlist\?list=)|youtu\.be/)[\w\-]+"
)


def is_valid_youtube_url(url: str) -> bool:
    return bool(YT_URL_PATTERN.match(url))


def _is_entry_available(entry: dict | None) -> bool:
    if entry is None:
        return False
    title = (entry.get("title") or "").lower()
    if not entry.get("url"):
        return False
    if any(keyword in title for keyword in ["[private", "[deleted", "[unavailable"]):
        return False
    return True


def detect_url_type(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") == "playlist":
        entries = info.get("entries", [])
        available = [e for e in entries if _is_entry_available(e)]
        total = info.get("playlist_count") or len(available)
        return {
            "type": "playlist",
            "title": info.get("title"),
            "count": total,
            "url": url,
            "entries": available,
        }
    return {
        "type": "video",
        "title": info.get("title"),
        "count": 1,
        "url": url,
        "entries": [info],
    }
