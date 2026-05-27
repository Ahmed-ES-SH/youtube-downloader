# AGENTS.md — YouTube Downloader

## Project Overview

A minimal CLI application for downloading YouTube videos and playlists.  
Single-process terminal tool. No web UI, no frontend.

## Tech Stack

- **Language:** Python 3.11+
- **Package manager:** pip + venv
- **Key dependencies:** yt-dlp, InquirerPy, rich, click, pydantic
- **Testing:** pytest, pytest-mock

## Project Structure

```
yt-downloader/
├── main.py                  # Entry point — click CLI
├── components/
│   ├── input_handler.py     # URL validation, type detection (video vs playlist)
│   ├── prompt_handler.py    # Interactive terminal prompts (InquirerPy)
│   ├── queue_manager.py     # Builds and processes download queue
│   ├── downloader.py        # Core download logic using yt-dlp
│   └── config_handler.py    # Read/write ~/.ytdl/config.json (Pydantic)
├── utils/
│   ├── logger.py            # Colored terminal output (rich)
│   └── retry.py             # Retry decorator with exponential backoff
├── tests/
│   ├── test_input_handler.py
│   ├── test_queue_manager.py
│   ├── test_downloader.py
│   ├── test_config_handler.py
│   └── test_integration.py
├── requirements.txt
├── AGENTS.md
├── PROJECT_PLAN.md
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**System dependency:** `ffmpeg` must be installed and in PATH.

## Run

```bash
# Interactive mode (default)
python main.py

# Pass URL directly
python main.py --url "https://youtube.com/watch?v=..."

# Use saved config without re-prompting
python main.py --url "..." --use-defaults
```

## Test

```bash
pytest tests/ -v
pytest tests/ -v --tb=short
pytest tests/ -v -k "queue"
```

## Lint / Type Check

```bash
pip install ruff mypy
ruff check .
mypy .
```

## Key Conventions

- **No comments in code** unless the task specifically requires them.
- **No new files** unless explicitly requested — prefer editing existing ones.
- **Error types:** `DownloadError` for download failures; retry with exponential backoff via `@with_retry`.
- **Config:** Pydantic model persisted as JSON at `~/.ytdl/config.json`.
- **State:** In-memory during session. No database, no server, no async/await.
- **Style:** Use `ruff` linting; default to `ruff format` for formatting.
- **Testing:** Mock `yt_dlp.YoutubeDL` in unit tests; prefer `pytest-mock`.

## Modes

| Flag | Behavior |
|------|----------|
| *(none)* | Full interactive mode with prompts |
| `--url` / `-u` | Skip URL prompt, still ask format/quality/path |
| `--use-defaults` | Skip all prompts, use saved config values |

## Common Tasks

- **Add new format option:** Update `prompt_handler.py` choices list and `downloader.py` `_build_opts` method.
- **Change config schema:** Edit `AppConfig` in `config_handler.py`; both files handle the model.
- **Add new error category:** Add handling in `main.py` queue loop and optional checks in `downloader.py`.
