import time
import json
import threading
import logging
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, unquote
import feedparser
from dateutil import parser as date_parser

import redis
from services.truth_loader import TruthLoader  # Vexy Truth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RSSLoader")

class RSSLoader(threading.Thread):
    MAX_AGE_DAYS = 3  # Skip items older than 3 days

    def __init__(self, redis_client, cfg: dict, logger=None):
        super().__init__(daemon=True)
        self.redis = redis_client
        self.cfg = cfg
        self.logger = logger or logging.getLogger("RSSLoader")
        self.group_name = cfg.get("name", "Unnamed RSS Group")
        self.interval = cfg.get("poll_interval_sec", 600)
        self.is_google = cfg.get("is_google_alerts", False)
        self.sources = cfg.get("sources", [])
        self.running = True

    def run(self):
        self.logger.info(
            f"🗞️ RSSLoader started for group '{self.group_name}' "
            f"with {len(self.sources)} sources, polling every {self.interval}s"
        )

        while self.running:
            start_time = datetime.now(timezone.utc)
            new_items, errors = 0, 0

            for src in self.sources:
                try:
                    name = src.get("name", "Unnamed Source")
                    url = src.get("url")

                    if not url:
                        self.logger.warning(f"[{self.group_name}] Missing URL for source {name}")
                        continue

                    feed = feedparser.parse(url)
                    entries = feed.entries if hasattr(feed, "entries") else []

                    if not entries:
                        self.logger.warning(f"[{self.group_name}] No entries found for {name}")
                        continue

                    for entry in entries:
                        try:
                            published_str = entry.get("published", "") or entry.get("pubDate", "")
                            try:
                                published_dt = date_parser.parse(published_str)
                                age_days = (datetime.now(timezone.utc) - published_dt).days
                                if age_days > self.MAX_AGE_DAYS:
                                    self.logger.debug(f"[{self.group_name}] Skipped stale entry ({published_str})")
                                    continue
                            except Exception:
                                self.logger.debug(f"[{self.group_name}] Could not parse date for entry from {name}")

                            item_url = self._extract_target_url(entry, is_google=self.is_google)
                            if not item_url:
                                continue

                            uid = hashlib.sha256(item_url.encode("utf-8")).hexdigest()
                            redis_key = f"truth:feed:rss:{self.group_name}:{uid}"

                            item_payload = {
                                "group": self.group_name,
                                "source": name,
                                "title": entry.get("title", "untitled"),
                                "url": item_url,
                                "published": published_str,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }

                            self.redis.set(redis_key, json.dumps(item_payload))
                            self.redis.expire(redis_key, self.interval * 2)
                            new_items += 1

                        except Exception as item_err:
                            errors += 1
                            self.logger.error(f"[{self.group_name}] Failed to process entry in {name}: {item_err}")

                except Exception as e:
                    errors += 1
                    self.logger.error(f"[{self.group_name}] Error processing {src}: {e}")

            metrics = {
                "group": self.group_name,
                "status": "ok" if errors == 0 else "degraded",
                "new_items": new_items,
                "errors": errors,
                "sources_checked": len(self.sources),
                "last_poll": datetime.now(timezone.utc).isoformat(),
            }
            self.redis.set(f"truth:feed:rss:metrics:{self.group_name}", json.dumps(metrics))
            self.logger.info(f"[{self.group_name}] 🧾 Metrics: {new_items} new, {errors} errors.")

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            sleep_for = max(5, self.interval - elapsed)
            time.sleep(sleep_for)

    def stop(self):
        self.running = False
        self.logger.info(f"🛑 RSSLoader stopped for group '{self.group_name}'.")

    def _extract_target_url(self, entry, is_google: bool = False) -> str:
        try:
            if not entry:
                return None

            link = entry.get("link") or entry.get("id")
            if not link:
                return None

            if is_google:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                target = params.get("url") or params.get("q")
                if target:
                    return unquote(target[0])
            return link
        except Exception as e:
            self.logger.warning(f"URL extraction failed: {e}")
            return None

# Vexy orchestrator for multiple groups
class RSSOrchestrator:
    def __init__(self, redis_client):
        self.redis = redis_client
        loader = TruthLoader(self.redis)
        schema = loader.load_schema()
        self.rss_config = schema["providers"]["rss_feeds"]
        self.ingestors = []

    def start(self):
        for group_name, group_cfg in self.rss_config.items():
            if group_cfg.get("enabled", False):
                ingestor = RSSLoader(self.redis, group_cfg)
                ingestor.start()
                self.ingestors.append(ingestor)
                print(f"Started RSS ingestor for {group_name}")

    def stop(self):
        for ingestor in self.ingestors:
            ingestor.stop()

# Quick run for milestone
if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    orchestrator = RSSOrchestrator(r)
    orchestrator.start()
    try:
        while True:
            time.sleep(1)  # Keep alive for daemon threads
    except KeyboardInterrupt:
        orchestrator.stop()