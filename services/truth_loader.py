import json
import redis
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

class TruthLoader:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logging.getLogger("TruthLoader")

    def load_schema(self, json_path="config/canonical_truth.json"):
        with open(json_path, 'r') as f:
            schema = json.load(f)
        schema["loaded_ts"] = datetime.now(ZoneInfo("UTC")).isoformat()
        self.redis.set("truth:integration:schema", json.dumps(schema))
        self.logger.info("✅ Truth schema loaded to Redis – single mirror live")
        return schema

# Quick run
if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    loader = TruthLoader(r)
    schema = loader.load_schema()
    print("Schema symbols:", schema["chainfeed"]["default_symbols"])