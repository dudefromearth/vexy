from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

class LastQuote(BaseModel):
    ask: Optional[float] = 0.0
    ask_size: Optional[int] = 0
    ask_exchange: Optional[int] = 0
    bid: Optional[float] = 0.0
    bid_size: Optional[int] = 0
    bid_exchange: Optional[int] = 0
    last_updated: Optional[int] = 0
    midpoint: Optional[float] = 0.0
    timeframe: str = "REAL-TIME"

class LastTrade(BaseModel):
    sip_timestamp: Optional[int] = 0
    conditions: List[int] = []
    price: Optional[float] = 0.0
    size: Optional[int] = 0
    exchange: Optional[int] = 0
    timeframe: str = "REAL-TIME"

class Day(BaseModel):
    close: Optional[float] = 0.0
    high: Optional[float] = 0.0
    last_updated: Optional[int] = 0
    low: Optional[float] = 0.0
    open: Optional[float] = 0.0
    volume: Optional[int] = 0
    vwap: Optional[float] = 0.0

class Details(BaseModel):
    contract_type: str = "call"
    exercise_style: str = "american"
    expiration_date: str = ""
    shares_per_contract: int = 100
    strike_price: float = 0.0
    ticker: str = ""

class Greeks(BaseModel):
    delta: Optional[float] = 0.0
    gamma: Optional[float] = 0.0
    theta: Optional[float] = 0.0
    vega: Optional[float] = 0.0

class UnderlyingAsset(BaseModel):
    ticker: str = "SPY"
    price: Optional[float] = 0.0
    change_to_break_even: Optional[float] = 0.0
    last_updated: Optional[int] = 0

class OptionContract(BaseModel):
    break_even_price: Optional[float] = 0.0
    day: Optional[Day] = None
    details: Details
    greeks: Greeks = Greeks()  # Default empty
    implied_volatility: Optional[float] = 0.0
    last_quote: Optional[LastQuote] = None
    last_trade: Optional[LastTrade] = None
    open_interest: Optional[int] = 0
    underlying_asset: Optional[UnderlyingAsset] = None

class ChainFeed(BaseModel):
    symbol: str
    source: str = "Polygon"
    feed_type: str = "raw"
    frame_ts: str = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")).isoformat())
    count: int = 0
    contracts: List[OptionContract] = []
    metadata: Dict[str, Any] = {}

    def to_json(self) -> str:
        return self.model_dump_json()