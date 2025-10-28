from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

class RSSFeed(BaseModel):
    feed_type: str = "rss"
    frame_ts: str = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")).isoformat())
    count: int = 0
    entries: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    def to_json(self) -> str:
        return self.model_dump_json()