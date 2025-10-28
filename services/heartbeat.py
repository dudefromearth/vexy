import time
import json
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import redis

class HeartbeatPublisher(threading.Thread):
    def __init__(self, redis_client, node_id: str = "studiotwo", interval_sec: int = 15):
        super().__init__(daemon=True)
        self.redis = redis_client
        self.node_id = node_id
        self.interval = interval_sec
        self.running = True
        self.uptime_start = time.time()

    def run(self):
        while self.running:
            ts = datetime.now(ZoneInfo("UTC")).isoformat()
            uptime = time.time() - self.uptime_start
            heartbeat = {
                "node_id": self.node_id,
                "status": "alive",
                "timestamp": ts,
                "uptime_sec": uptime
            }
            key = f"truth:heartbeat:{self.node_id}"
            self.redis.set(key, json.dumps(heartbeat), ex=self.interval * 2)
            self.redis.publish("mesh:heartbeat", json.dumps(heartbeat))
            print(f"💓 Heartbeat published → {key} (uptime: {uptime:.0f}s)")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

# Test
if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    hb = HeartbeatPublisher(r)
    hb.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hb.stop()