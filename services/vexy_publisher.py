import json
import redis
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def publish_commentary(output: dict):
    channel = "market:commentary"
    r.publish(channel, json.dumps(output))
    print(f"Vexy published to {channel}: {output['insight'][:50]}...")

# Test
if __name__ == "__main__":
    sample_output = {"timestamp": "2025-10-28T14:00:00Z", "snapshot": {"SPY": {"price": 523.45}}, "insight": "SPY's plunging on bond yield spikes—grab those puts before Fed's Powell drops the rate bomb!"}
    publish_commentary(sample_output)