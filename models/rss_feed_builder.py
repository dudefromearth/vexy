from typing import List, Dict, Any
from models.abstract_builder import AbstractBuilder
from models.rss_feed import RSSFeed
from datetime import datetime
from zoneinfo import ZoneInfo

class RSSFeedBuilder(AbstractBuilder):
    def __init__(self):
        self.data = {}

    def with_group(self, group: str):
        self.data["group"] = group
        return self

    def with_entries(self, entries: List[Dict[str, Any]]):
        self.data["entries"] = entries
        self.data["count"] = len(entries)
        return self

    def with_metadata(self, metadata: Dict[str, Any]):
        self.data["metadata"] = metadata
        return self

    def build(self) -> RSSFeed:
        self.data["frame_ts"] = datetime.now(ZoneInfo("UTC")).isoformat()
        return RSSFeed(**self.data)