from pathlib import Path

import yt_dlp

from utils.retry import with_retry


class DownloadError(Exception):
    pass


class Downloader:
    def __init__(self):
        pass

    def _build_opts(self, options: dict) -> dict:
        fmt = options.get("format", "video")
        quality = options.get("quality", "best")
        output_path = options.get("output", str(Path.home() / "Downloads" / "ytdl"))
        audio_bitrate = options.get("audio_bitrate", "192")

        outtmpl = str(Path(output_path) / "%(title)s.%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
        }

        if fmt == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_bitrate,
                }],
            })
        else:
            if quality == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                ydl_opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

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

    def _progress_hook(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = downloaded / total * 100
                print(f"  \r  Downloading... {pct:.1f}%", end="", flush=True)
        elif d.get("status") == "finished":
            print(f"  \r  Download complete")

    @with_retry(max_attempts=3, delay=2.0)
    def download(self, item, options: dict):
        try:
            with yt_dlp.YoutubeDL(self._build_opts(options)) as ydl:
                ydl.download([item.url])
        except Exception as e:
            raise DownloadError(str(e)) from e
