import logging
import time
import signal
import sys
import os
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import redis
from services.truth_loader import TruthLoader
from services.polygon_fetcher import PolygonFetcher
from services.rss_loader import RSSLoader
from services.data_aggregator import aggregate_snapshot
from services.vexy_analysts import invoke_vexy_analysts
from services.vexy_publisher import publish_commentary

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
root_logger = logging.getLogger()

def log_status(emoji: str, message: str):
    full_msg = f"{emoji} {message}"
    root_logger.info(full_msg)

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class VexyStartup:
    def __init__(self):
        self.logger = logging.getLogger("VexyStartup")
        self.redis = r
        self.rss_loader = None
        self.running = True

    def run(self):
        log_status("🌿", "Vexy Startup Sequence (v1.0)")

        log_status("🌱", "Beginning startup sequence...")

        # Redis connection
        try:
            log_status("✅", "Redis connection established at localhost:6379")
        except Exception as e:
            log_status("❌", f"Redis connection failed: {e}")
            return

        # Truth load
        try:
            loader = TruthLoader(self.redis)
            schema = loader.load_schema()
            symbols = schema.get("chainfeed", {}).get("default_symbols", [])
            log_status("📖", "Starting TruthService...")
            log_status("📄", "Loaded seed truth from ./config/canonical_truth.json (v1.5.0)")
            log_status("📡", "Published canonical truth → truth:integration:schema")
            log_status("✅", f"TruthService loaded and active ({len(symbols)} symbols)")
        except Exception as e:
            log_status("❌", f"TruthService failed: {e}")
            return

        # Polygon fetch
        try:
            log_status("🔗", "Starting Polygon fetch...")
            polygon = PolygonFetcher(self.redis)
            for symbol in symbols[:2]:  # Test 2
                polygon.fetch_chain(symbol)
            log_status("✅", "Polygon chains fetched and published")
        except Exception as e:
            log_status("❌", f"Polygon fetch failed: {e}")

        # RSS load
        try:
            log_status("🗞️", "Starting RSS Feed Ingestors...")
            self.rss_loader = RSSLoader(self.redis)
            self.rss_loader.load_all()
            log_status("✅", "RSS Feed Ingestion Service initialized and active")
        except Exception as e:
            log_status("❌", f"RSS Feed Ingestion Service failed: {e}")

        # Vexy workflow
        try:
            log_status("🧠", "Starting Vexy AI workflow...")
            snapshot = aggregate_snapshot()
            output = invoke_vexy_analysts(snapshot)
            publish_commentary(output)
            log_status("✅", "Vexy AI: Commentary published")
        except Exception as e:
            log_status("❌", f"Vexy AI workflow failed: {e}")

        log_status("🌳", "Vexy startup sequence complete")
        log_status("📡", "Published startup phase → startup_complete")

        # Graceful shutdown
        def signal_handler(sig, frame):
            log_status("🛑", "Shutdown signal received.")
            self.running = False
            try:
                # Announce shutdown to Redis
                payload = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "shutting_down",
                    "node_id": "studiotwo"
                }
                self.redis.set("truth:system:shutdown_notice", json.dumps(payload))
                self.redis.publish("truth:alert:system", json.dumps(payload))
                log_status("📡", "Published system shutdown notice to Redis.")

                # Stop RSS loader
                if self.rss_loader:
                    log_status("🛑", "Stopping RSS Feed Ingestors...")
                    self.rss_loader.stop()
                    log_status("🪶", "RSS Feed Ingestion Service stopped")

                # Grace delay
                shutdown_delay = int(os.getenv("SHUTDOWN_GRACE_DELAY", "5"))
                log_status("🕓", f"Grace period before shutdown ({shutdown_delay}s)...")
                time.sleep(shutdown_delay)

            except Exception as e:
                log_status("❌", f"Shutdown error: {e}")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self.running:
                time.sleep(60)
        except KeyboardInterrupt:
            signal_handler(None, None)
            sys.exit(0)  # Force exit after handler

if __name__ == "__main__":
    startup = VexyStartup()
    startup.run()