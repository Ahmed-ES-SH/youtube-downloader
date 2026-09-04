from unittest.mock import MagicMock, patch

import pytest

from components.downloader import Downloader, DownloadError
from components.queue_manager import QueueItem


@patch("components.downloader.yt_dlp.YoutubeDL")
def test_download_success(mock_ydl):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance

    downloader = Downloader()
    item = QueueItem(index=1, title="Test Video", url="https://yt.com/test")
    options = {"format": "video", "quality": "best", "output": "/tmp"}

    downloader.download(item, options)
    mock_instance.download.assert_called_once_with(["https://yt.com/test"])


@patch("components.downloader.yt_dlp.YoutubeDL")
def test_download_with_trim(mock_ydl):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance

    downloader = Downloader()
    item = QueueItem(index=1, title="Test Video", url="https://yt.com/test")
    options = {
        "format": "video",
        "quality": "best",
        "output": "/tmp",
        "trim": {"start_time": "1:30", "end_time": "2:45"},
    }

    downloader.download(item, options)
    mock_instance.download.assert_called_once_with(["https://yt.com/test"])
    opts = mock_ydl.call_args[0][0]
    assert opts["postprocessor_args"] == {
        "ffmpeg": ["-ss", "1:30", "-to", "2:45"],
        "ffmpegav": ["-ss", "1:30", "-to", "2:45"],
    }


@patch("components.downloader.yt_dlp.YoutubeDL")
def test_download_failure_raises(mock_ydl):
    mock_instance = MagicMock()
    mock_instance.download.side_effect = Exception("Network error")
    mock_ydl.return_value.__enter__.return_value = mock_instance

    downloader = Downloader()
    item = QueueItem(index=1, title="Test Video", url="https://yt.com/test")
    options = {"format": "video", "quality": "best", "output": "/tmp"}

    with pytest.raises(DownloadError):
        downloader.download(item, options)
