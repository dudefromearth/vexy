from datetime import datetime
from zoneinfo import ZoneInfo  # Added import
from typing import Dict, Any  # Added import

from models.abstract_builder import AbstractBuilder  # Full path if needed

class ChainFeedConcreteBuilder(AbstractBuilder):
    def __init__(self):
        self.data = {}

    def with_symbol(self, symbol: str):
        self.data["symbol"] = symbol
        return self

    def with_contracts(self, contracts: list):
        self.data["contracts"] = contracts
        self.data["count"] = len(contracts)
        return self

    def with_metadata(self, metadata: dict):
        self.data["metadata"] = metadata
        return self

    def build(self) -> Dict[str, Any]:  # Typed return
        self.data["frame_ts"] = datetime.now(ZoneInfo("UTC")).isoformat()
        self.data["feed_type"] = "raw"
        self.data["source"] = "Polygon"
        return self.data