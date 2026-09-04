from unittest.mock import MagicMock, patch

from components.downloader import Downloader
from components.queue_manager import QueueManager

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
        downloader.download(
            item, {"format": "video", "quality": "best", "output": "/tmp"}
        )
        queue.mark_done(item)

    summary = queue.summary()
    assert summary["done"] == 2
    assert summary["failed"] == 0
    assert mock_instance.download.call_count == 2
