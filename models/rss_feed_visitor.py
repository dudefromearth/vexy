from typing import Dict, Any, List
from models.abstract_visitor import AbstractVisitor

class RSSFeedVisitor(AbstractVisitor):
    def visit_recent_entries(self, feed: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        entries = feed.get("entries", [])
        return entries[:limit]

    def visit_by_author(self, feed: Dict[str, Any], author: str) -> List[Dict[str, Any]]:
        entries = feed.get("entries", [])
        return [e for e in entries if e.get("author", "").lower() == author.lower()]

    def visit_chain(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "recent": self.visit_recent_entries(feed),
            "totals": {"count": feed.get("count", 0), "authors": len(set(e.get("author", "") for e in feed.get("entries", [])))}
        }