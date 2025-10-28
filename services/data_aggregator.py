import json
import redis
from datetime import datetime
from zoneinfo import ZoneInfo

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def aggregate_snapshot(symbol: str = "SPY", rss_group: str = "Jerome Powell") -> dict:
    # Pull chain from Redis
    chain_key = f"truth:chain:raw:{symbol}"
    chain_json = r.get(chain_key)
    if not chain_json:
        return {"error": "No chain data in Redis"}
    chain = json.loads(chain_json)
    spot = chain.get("spot_price", 523.45)  # Stub from metadata if missing

    # Pull RSS from Redis
    rss_key = f"truth:feed:rss:{rss_group}"
    rss_json = r.get(rss_key)
    rss = json.loads(rss_json or "[]")
    headline = rss[0].get("title", "Market quiet") if rss else "Market quiet"

    # Aggregate snapshot
    snapshot = {
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
        "market_snapshot": {symbol: {"price": spot, "change": -0.35, "vol": 1.2}},  # Stub derived for now
        "headline": headline
    }
    return snapshot

# Test
if __name__ == "__main__":
    snapshot = aggregate_snapshot()
    print("Aggregated snapshot:", json.dumps(snapshot, indent=2))