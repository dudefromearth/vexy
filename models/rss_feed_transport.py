import json
from datetime import datetime
from zoneinfo import ZoneInfo
from models.transport import Transport
from typing import List, Dict, Any

class RSSFeedTransport(Transport):
    def wrap(self, raw_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "feed_type": "rss",
            "frame_ts": datetime.now(ZoneInfo("UTC")).isoformat(),
            "count": len(raw_entries),
            "entries": raw_entries,
            "metadata": {"fetched_at": datetime.now(ZoneInfo("UTC")).isoformat()}
        }

    def serialize(self, data: Dict[str, Any]) -> str:
        return json.dumps(data)

    def deserialize(self, json_str: str) -> Dict[str, Any]:
        return json.loads(json_str)