from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any
from models.abstract_assembler import AbstractAssembler

class ChainFeedAssembler(AbstractAssembler):
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

    def assemble(self) -> Dict[str, Any]:
        self.data["frame_ts"] = datetime.now(ZoneInfo("UTC")).isoformat()
        self.data["feed_type"] = "raw"
        self.data["source"] = "Polygon"
        return self.data