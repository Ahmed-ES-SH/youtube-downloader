from pathlib import Path

import yt_dlp

from utils.logger import get_progress
from utils.retry import with_retry


class DownloadError(Exception):
    pass


class Downloader:
    def __init__(self):
        self._progress = None
        self._task_id = None

    def _build_opts(self, options: dict) -> dict:
        fmt = options.get("format", "video")
        quality = options.get("quality", "best")
        output_path = options.get("output", str(Path.home() / "Downloads" / "ytdl"))
        audio_bitrate = options.get("audio_bitrate", "192")

        output_dir = Path(output_path).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(output_dir / "%(title)s.%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "continuedl": True,
            "geo_bypass": True,
            "progress_hooks": [self._progress_hook],
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "windowsfilenames": True,
        }

        if fmt == "audio":
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": audio_bitrate,
                        }
                    ],
                }
            )
        else:
            ydl_opts["merge_output_format"] = "mp4"
            if quality == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                q = quality.replace("p", "")
                ydl_opts["format"] = (
                    f"bestvideo[height<={q}]+bestaudio/best[height<={q}]/bestvideo[height<={q}]/best"
                )

        playlist_items = options.get("playlist_items")
        if playlist_items:
            ydl_opts["playlist_items"] = playlist_items

        trim = options.get("trim")
        if trim:
            ydl_opts["postprocessor_args"] = {
                "ffmpeg": ["-ss", trim["start_time"], "-to", trim["end_time"]],
                "ffmpegav": ["-ss", trim["start_time"], "-to", trim["end_time"]],
            }

        return ydl_opts

    def _progress_hook(self, d: dict):
        if self._progress is None or self._task_id is None:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                self._progress.update(self._task_id, total=total, completed=downloaded)
        elif status == "finished":
            self._progress.update(
                self._task_id,
                description="[bold green]Processing...",
                completed=100,
                total=100,
            )

    @with_retry(max_attempts=3, delay=2.0)
    def download(self, item, options: dict):
        try:
            with get_progress() as progress:
                self._progress = progress
                title = item.title if len(item.title) <= 35 else f"{item.title[:32]}..."
                self._task_id = progress.add_task(f"Downloading {title}", total=None)
                with yt_dlp.YoutubeDL(self._build_opts(options)) as ydl:
                    ydl.download([item.url])
        except Exception as e:
            raise DownloadError(str(e)) from e
        finally:
            self._progress = None
            self._task_id = None
