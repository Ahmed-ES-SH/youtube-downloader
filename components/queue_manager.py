from dataclasses import dataclass
from enum import Enum


class ItemStatus(Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


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
            QueueItem(
                index=i + 1,
                title=e.get("title", "Unknown"),
                url=e.get("url") or e.get("webpage_url"),
            )
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
