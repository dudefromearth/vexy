import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import redis
from services.truth_loader import TruthLoader  # Your loader class

class PolygonFetcher:
    def __init__(self, redis_client):
        self.redis = redis_client
        loader = TruthLoader(self.redis)
        schema = loader.load_schema()  # Reload if needed
        cfg = schema["providers"]["data_providers"]["polygon_api"]
        self.api_key = cfg["api_key"]
        self.base_url = cfg["base_url"]

    def fetch_chain(self, symbol: str = "SPY") -> str:  # Returns JSON string for Redis
        url = f"{self.base_url}/{symbol}"  # Fixed: Path param /SPY
        params = {"apiKey": self.api_key}  # Removed limit – default 100
        try:
            resp = requests.get(url, params=params, timeout=10)
            print(f"API Response Status: {resp.status_code}")  # Debug
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])

            contracts = []
            for opt in results:
                contracts.append({
                    "strike": opt.get("strike_price", 0),
                    "expiry": opt.get("expiration_date", ""),
                    "bid": opt.get("last_quote", {}).get("bid", 0),
                    "ask": opt.get("last_quote", {}).get("ask", 0),
                    "volume": opt.get("volume", 0),
                    "open_interest": opt.get("open_interest", 0)
                })

            feed = {
                "symbol": symbol,
                "source": "Polygon",
                "feed_type": "raw",
                "frame_ts": datetime.now(ZoneInfo("UTC")).isoformat(),
                "count": len(contracts),
                "contracts": contracts,
                "metadata": {
                    "api_size": len(results),
                    "fetched_at": datetime.now(ZoneInfo("UTC")).isoformat()
                }
            }

            key = f"truth:chain:raw:{symbol}"
            self.redis.set(key, json.dumps(feed), ex=300)
            self.redis.hset(f"truth:metrics:chain:{symbol}", mapping={
                "latency_ms": resp.elapsed.total_seconds() * 1000,
                "count": len(contracts),
                "ts": feed["frame_ts"]
            })

            print(f"✅ Chain fetched & published: {symbol}, count={feed['count']}")
            return json.dumps(feed)

        except requests.RequestException as e:
            print(f"⚠️ API error for {symbol}: {e} – using mock fallback")
            mock_feed = {
                "symbol": symbol,
                "source": "mock",
                "feed_type": "raw",
                "frame_ts": datetime.now(ZoneInfo("UTC")).isoformat(),
                "count": 2,
                "contracts": [
                    {"strike": 450.0, "expiry": "2025-10-28", "bid": 1.5, "ask": 1.6, "volume": 100, "open_interest": 500},
                    {"strike": 455.0, "expiry": "2025-10-28", "bid": 0.8, "ask": 0.9, "volume": 200, "open_interest": 300}
                ],
                "metadata": {"mode": "mock", "error": str(e)}
            }
            key = f"truth:chain:raw:{symbol}"
            self.redis.set(key, json.dumps(mock_feed), ex=300)
            return json.dumps(mock_feed)

# Quick run for milestone
if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    fetcher = PolygonFetcher(r)
    feed_json = fetcher.fetch_chain("SPY")
    print("Published JSON:", feed_json[:200] + "...")  # Snippet