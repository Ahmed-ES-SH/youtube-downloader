# Terminal YouTube Downloader — Project Plan

> A minimal, fast-to-build CLI application for downloading YouTube videos and playlists.
> No web UI. No frontend. Pure terminal.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [CLI Flow Design](#3-cli-flow-design)
4. [Download Queue System](#4-download-queue-system)
5. [Configuration Handling](#5-configuration-handling)
6. [Error Handling Strategy](#6-error-handling-strategy)
7. [Testing Phase](#7-testing-phase)
8. [Build & Run Instructions](#8-build--run-instructions)
9. [Simplicity Constraints](#9-simplicity-constraints)

---

## 1. Architecture Overview

### Design Philosophy

- Single-process CLI tool — no server, no daemon, no background service
- Each component is a separate module (file/class), not a microservice
- State is held in memory during a session; config persisted to a single JSON file

### Component Map

```
yt-downloader/
├── main.py                  # Entry point — wires everything together
├── components/
│   ├── input_handler.py     # URL validation, type detection (video vs playlist)
│   ├── prompt_handler.py    # Interactive terminal prompts (format, quality, path)
│   ├── queue_manager.py     # Builds and processes the download queue
│   ├── downloader.py        # Core download logic using yt-dlp
│   └── config_handler.py    # Read/write ~/.ytdl/config.json
├── utils/
│   ├── logger.py            # Colored terminal output, progress display
│   └── retry.py             # Retry decorator with backoff
├── tests/
│   ├── test_input_handler.py
│   ├── test_queue_manager.py
│   ├── test_downloader.py
│   └── test_config_handler.py
├── requirements.txt
└── README.md
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| `input_handler` | Validate URL, detect video vs playlist, extract metadata |
| `prompt_handler` | Ask user for format, quality, output path interactively |
| `queue_manager` | Build queue from playlist items, iterate sequentially |
| `downloader` | Call yt-dlp, handle hooks for progress, manage output path |
| `config_handler` | Load/save user preferences to `~/.ytdl/config.json` |

---

## 2. Technology Stack

### Primary Language: **Python 3.11+**

Chosen for: fastest implementation speed, mature yt-dlp bindings, rich CLI libraries, easy packaging.

### Core Dependencies

| Package | Purpose | Why |
|---|---|---|
| `yt-dlp` | YouTube downloading engine | Actively maintained fork of youtube-dl, supports all formats/qualities |
| `InquirerPy` | Interactive terminal prompts | Clean arrow-key menus, no manual input parsing |
| `rich` | Terminal output, progress bars, tables | Best-in-class terminal UI without being a framework |
| `click` | CLI argument parsing (optional flags) | Simple, production-standard, zero boilerplate |
| `pydantic` | Config schema validation | Clean model for config.json, free validation |

### Dev/Test Dependencies

| Package | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-mock` | Mock yt-dlp calls |
| `responses` / `unittest.mock` | Mock network layer |
| `pyinstaller` | Package into single binary (optional) |

### Install

```bash
pip install yt-dlp InquirerPy rich click pydantic
pip install --dev pytest pytest-mock
```

---

## 3. CLI Flow Design

### Launch Modes

```bash
# Interactive mode (default)
python main.py

# Pass URL directly (skip first prompt)
python main.py --url "https://youtube.com/watch?v=..."

# Use saved config without re-prompting
python main.py --url "..." --use-defaults
```

### Full Interactive Terminal Flow

```
╔══════════════════════════════════════╗
║       YouTube Terminal Downloader    ║
╚══════════════════════════════════════╝

? Enter YouTube URL: https://www.youtube.com/playlist?list=PLxxx

  ✔ Detected: Playlist — "Lo-Fi Coding Music" (24 videos)

? Select download format:
  ❯ Video (MP4)
    Audio only (MP3)

? Select quality:
  ❯ Best available
    1080p
    720p
    480p
    360p

  [Only shown for Audio only]:
? Select audio bitrate:
  ❯ 320kbps
    192kbps
    128kbps

? Output folder:
  ❯ Use default  (~/.ytdl/downloads)
    Enter custom path

  [If custom path]:
? Enter full path: /home/user/Music/lofi

─────────────────────────────────────────
  Ready to download 24 items to:
  /home/user/Music/lofi
─────────────────────────────────────────

? Confirm and start? (Y/n): Y

  Downloading [1/24] — "Track Name Here"
  ████████████████░░░░ 78% | 14.2 MB / 18.3 MB | ETA: 4s

  ✔ [1/24] Done
  Downloading [2/24] — "Another Track"
  ...

─────────────────────────────────────────
  ✔ 23 downloaded successfully
  ✗  1 failed — "Private Video" (skipped)
─────────────────────────────────────────
```

---

## 4. Download Queue System

### Playlist Extraction

```python
# components/input_handler.py

import yt_dlp

def detect_url_type(url: str) -> dict:
    """Returns metadata about the URL without downloading."""
    ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    if info.get("_type") == "playlist":
        return {
            "type": "playlist",
            "title": info.get("title"),
            "count": len(info.get("entries", [])),
            "entries": info.get("entries", [])
        }
    return {
        "type": "video",
        "title": info.get("title"),
        "count": 1,
        "entries": [info]
    }
```

### Queue Manager

```python
# components/queue_manager.py

from dataclasses import dataclass, field
from enum import Enum

class ItemStatus(Enum):
    PENDING  = "pending"
    DONE     = "done"
    FAILED   = "failed"
    SKIPPED  = "skipped"

@dataclass
class QueueItem:
    index: int
    title: str
    url: str
    status: ItemStatus = ItemStatus.PENDING
    error: str | None = None

class QueueManager:
    def __init__(self, entries: list[dict]):
        self.items: list[QueueItem] = [
            QueueItem(index=i + 1, title=e.get("title", "Unknown"), url=e.get("url") or e.get("webpage_url"))
            for i, e in enumerate(entries)
        ]

    def pending(self) -> list[QueueItem]:
        return [i for i in self.items if i.status == ItemStatus.PENDING]

    def mark_done(self, item: QueueItem):
        item.status = ItemStatus.DONE

    def mark_failed(self, item: QueueItem, error: str):
        item.status = ItemStatus.FAILED
        item.error = error

    def summary(self) -> dict:
        return {
            "total": len(self.items),
            "done": sum(1 for i in self.items if i.status == ItemStatus.DONE),
            "failed": sum(1 for i in self.items if i.status == ItemStatus.FAILED),
        }
```

### Sequential Processing (Default)

```python
# main.py (queue loop)

for item in queue.pending():
    try:
        downloader.download(item, options)
        queue.mark_done(item)
    except DownloadError as e:
        queue.mark_failed(item, str(e))
        if not ask_skip_or_abort():
            break
```

### Optional Concurrency (Phase 2 only)

If concurrency is needed later, use `concurrent.futures.ThreadPoolExecutor` with `max_workers=3`.
**Do not add this until single-threaded version is stable and tested.**

---

## 5. Configuration Handling

### Config File Location

```
~/.ytdl/config.json
```

### Config Schema (Pydantic)

```python
# components/config_handler.py

from pydantic import BaseModel
from pathlib import Path
import json

CONFIG_PATH = Path.home() / ".ytdl" / "config.json"

class AppConfig(BaseModel):
    default_output_path: str = str(Path.home() / "Downloads" / "ytdl")
    default_format: str = "video"       # "video" | "audio"
    default_quality: str = "best"       # "best" | "1080p" | "720p" | etc.
    default_audio_bitrate: str = "192"  # kbps
    remember_last: bool = True

def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
        return AppConfig(**data)
    return AppConfig()

def save_config(config: AppConfig):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config.model_dump_json(indent=2))
```

### Example `config.json`

```json
{
  "default_output_path": "/home/user/Downloads/ytdl",
  "default_format": "video",
  "default_quality": "1080p",
  "default_audio_bitrate": "192",
  "remember_last": true
}
```

---

## 6. Error Handling Strategy

### Error Categories & Responses

| Error Type | Detection | Action |
|---|---|---|
| Invalid URL | yt-dlp raises `DownloadError` on extraction | Show clear message, re-prompt |
| Network timeout | `socket.timeout` / yt-dlp retry exhaustion | Retry with backoff (3 attempts) |
| Private/blocked video | yt-dlp error message contains "Private" or HTTP 403 | Log, mark as skipped, continue queue |
| Partial playlist failure | Individual item fails | Ask user: skip item or abort all |
| Disk full | `OSError: No space left on device` | Abort immediately, show clear message |
| Bad output path | `FileNotFoundError` on path creation | Validate path before queue starts |

### Retry Decorator

```python
# utils/retry.py

import time
import functools

def with_retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            wait = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(f"  ⚠ Attempt {attempt} failed: {e}. Retrying in {wait:.0f}s...")
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator
```

### Usage in Downloader

```python
@with_retry(max_attempts=3, delay=2.0)
def download(self, item: QueueItem, options: dict):
    with yt_dlp.YoutubeDL(self._build_opts(options)) as ydl:
        ydl.download([item.url])
```

### URL Validation (before queue starts)

```python
import re

YT_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|playlist\?list=)|youtu\.be/)[\w\-]+"
)

def is_valid_youtube_url(url: str) -> bool:
    return bool(YT_URL_PATTERN.match(url))
```

---

## 7. Testing Phase

### Unit Tests

#### `test_input_handler.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from components.input_handler import detect_url_type, is_valid_youtube_url

def test_valid_video_url():
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

def test_valid_playlist_url():
    assert is_valid_youtube_url("https://www.youtube.com/playlist?list=PLxxx") is True

def test_invalid_url():
    assert is_valid_youtube_url("https://vimeo.com/123456") is False

def test_empty_url():
    assert is_valid_youtube_url("") is False

@patch("components.input_handler.yt_dlp.YoutubeDL")
def test_detect_playlist(mock_ydl):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        "_type": "playlist",
        "title": "Test Playlist",
        "entries": [{"title": "Vid 1", "url": "..."}, {"title": "Vid 2", "url": "..."}]
    }
    mock_ydl.return_value.__enter__.return_value = mock_instance

    result = detect_url_type("https://youtube.com/playlist?list=PLtest")
    assert result["type"] == "playlist"
    assert result["count"] == 2

@patch("components.input_handler.yt_dlp.YoutubeDL")
def test_detect_single_video(mock_ydl):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        "_type": "video",
        "title": "Single Video",
        "webpage_url": "https://youtube.com/watch?v=abc"
    }
    mock_ydl.return_value.__enter__.return_value = mock_instance

    result = detect_url_type("https://youtube.com/watch?v=abc")
    assert result["type"] == "video"
    assert result["count"] == 1
```

#### `test_queue_manager.py`

```python
from components.queue_manager import QueueManager, ItemStatus

MOCK_ENTRIES = [
    {"title": "Video 1", "url": "https://yt.com/1"},
    {"title": "Video 2", "url": "https://yt.com/2"},
    {"title": "Video 3", "url": "https://yt.com/3"},
]

def test_queue_builds_correctly():
    q = QueueManager(MOCK_ENTRIES)
    assert len(q.items) == 3
    assert q.items[0].title == "Video 1"

def test_pending_returns_all_at_start():
    q = QueueManager(MOCK_ENTRIES)
    assert len(q.pending()) == 3

def test_mark_done_reduces_pending():
    q = QueueManager(MOCK_ENTRIES)
    q.mark_done(q.items[0])
    assert len(q.pending()) == 2

def test_mark_failed_stores_error():
    q = QueueManager(MOCK_ENTRIES)
    q.mark_failed(q.items[1], "HTTP 403 Forbidden")
    assert q.items[1].status == ItemStatus.FAILED
    assert "403" in q.items[1].error

def test_summary_counts():
    q = QueueManager(MOCK_ENTRIES)
    q.mark_done(q.items[0])
    q.mark_done(q.items[1])
    q.mark_failed(q.items[2], "Private video")
    s = q.summary()
    assert s["done"] == 2
    assert s["failed"] == 1
    assert s["total"] == 3

def test_empty_playlist():
    q = QueueManager([])
    assert len(q.items) == 0
    assert len(q.pending()) == 0
    assert q.summary()["total"] == 0
```

#### `test_config_handler.py`

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from components.config_handler import load_config, save_config, AppConfig

def test_load_defaults_when_no_file():
    with patch("components.config_handler.CONFIG_PATH") as mock_path:
        mock_path.exists.return_value = False
        config = load_config()
        assert config.default_format == "video"
        assert config.default_quality == "best"

def test_load_from_existing_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "default_format": "audio",
        "default_quality": "720p",
        "default_audio_bitrate": "320",
        "default_output_path": "/tmp/test",
        "remember_last": True
    }))
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
```

### Integration Test (Mocked Download)

```python
# tests/test_integration.py

from unittest.mock import patch, MagicMock
from components.queue_manager import QueueManager
from components.downloader import Downloader

MOCK_ENTRIES = [
    {"title": "Video A", "url": "https://yt.com/a"},
    {"title": "Video B", "url": "https://yt.com/b"},
]

@patch("components.downloader.yt_dlp.YoutubeDL")
def test_full_queue_processes_all(mock_ydl):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance

    queue = QueueManager(MOCK_ENTRIES)
    downloader = Downloader()

    for item in queue.pending():
        downloader.download(item, {"format": "video", "quality": "best", "output": "/tmp"})
        queue.mark_done(item)

    summary = queue.summary()
    assert summary["done"] == 2
    assert summary["failed"] == 0
    assert mock_instance.download.call_count == 2
```

### Manual CLI Testing Checklist

```
[ ] Single video URL — video format — best quality — default path
[ ] Single video URL — audio format — 320kbps — custom path
[ ] Playlist URL — video — 720p — default path
[ ] Playlist URL — audio — 192kbps — custom path
[ ] Invalid URL input — expect clear error message and re-prompt
[ ] Playlist with one private video — expect skip and continue
[ ] No internet connection — expect retry 3x then fail gracefully
[ ] Empty playlist URL — expect "No videos found" message
[ ] Disk full simulation — expect abort with clear message
[ ] Run twice — second run uses saved config as defaults
[ ] Pass --url flag directly — should skip URL prompt
[ ] Pass --use-defaults flag — should skip all prompts
```

### Edge Cases Matrix

| Scenario | Expected Behavior |
|---|---|
| URL to deleted video | yt-dlp raises error → skip with message |
| URL to private video | HTTP 403 → skip with "Private video" message |
| Playlist with 0 entries | Show "Playlist appears to be empty" → exit cleanly |
| Malformed URL (no protocol) | Regex fails → prompt user to re-enter |
| Path with no write permission | `PermissionError` → show message, ask for new path |
| Network drops mid-download | Retry up to 3x with exponential backoff |
| Ctrl+C during download | Catch `KeyboardInterrupt` → show summary of completed items |

---

## 8. Build & Run Instructions

### Requirements

- Python 3.11+
- `ffmpeg` installed and available in PATH (required by yt-dlp for format merging)

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### Setup

```bash
git clone https://github.com/yourname/yt-downloader.git
cd yt-downloader

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### `requirements.txt`

```
yt-dlp>=2024.1.0
InquirerPy>=0.3.4
rich>=13.0.0
click>=8.1.0
pydantic>=2.0.0
```

### Run

```bash
# Interactive mode
python main.py

# Pass URL directly
python main.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Use saved defaults (no prompts)
python main.py --url "https://..." --use-defaults
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/ -v --tb=short        # compact tracebacks
pytest tests/ -v -k "queue"        # run only queue tests
```

### Package as Executable Binary (Optional)

```bash
pip install pyinstaller

pyinstaller --onefile --name ytdl main.py

# Output binary at:
# dist/ytdl  (Linux/macOS)
# dist/ytdl.exe  (Windows)
```

Move to PATH for global access:

```bash
sudo mv dist/ytdl /usr/local/bin/ytdl
ytdl --url "https://..."
```

---

## 9. Simplicity Constraints

| Rule | Rationale |
|---|---|
| No web server, no REST API | This is a terminal tool — zero HTTP surface |
| No database | Config is a single JSON file; session state is in-memory |
| No message queue / Redis | Sequential queue is sufficient for this use case |
| No Docker | Not needed for a local CLI tool |
| No async/await (Phase 1) | Synchronous yt-dlp calls are simpler to reason about and debug |
| No plugin system | Direct function calls; extensibility can come later if needed |
| Single process | No workers, no subprocesses spawned manually |

### Implementation Timeline (Estimate)

| Phase | Tasks | Time |
|---|---|---|
| Phase 1 | input_handler + prompt_handler + basic downloader | 1–2 days |
| Phase 2 | queue_manager + config_handler + retry logic | 1 day |
| Phase 3 | rich terminal output + progress hooks | 0.5 days |
| Phase 4 | Unit + integration tests | 1 day |
| Phase 5 | Polish CLI (click flags, --use-defaults) + packaging | 0.5 days |
| **Total** | | **~4–5 days** |

---

