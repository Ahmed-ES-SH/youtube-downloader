from components.queue_manager import ItemStatus, QueueManager

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
