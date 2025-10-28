import time
import openai
import json
import os
import redis
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VexyWorkflow")

class VexyWorkflow:
    def __init__(self):
        from services.truth_loader import TruthLoader  # Load Truth
        loader = TruthLoader(r)
        schema = loader.load_schema()
        self.vexy_cfg = schema["convexity"]["agent"]
        self.model = self.vexy_cfg["openai_model"]
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.sub_data = {}  # Aggregated feeds
        self.pub_channel = "market:commentary"

    def startup(self):
        logger.info("🧠 Vexy AI startup – subbing feeds for aggregation")
        pubsub = r.pubsub()
        pubsub.subscribe("truth:chain:raw:*", "truth:feed:rss:*")  # Sub chains/RSS
        for message in pubsub.listen():
            if message['type'] == 'message':
                event = json.loads(message['data'])
                channel = message['channel']
                self.sub_data[channel] = event
                logger.info(f"Vexy sub: {channel} – {event.get('symbol', event.get('title', 'Data'))}")

    def aggregate_data(self) -> dict:
        # Prep prompt from sub_data (stub derived for now)
        chain = self.sub_data.get("truth:chain:raw:SPY", {})
        spot = chain.get("spot_price", 523.45)
        rss = self.sub_data.get("truth:feed:rss:Jerome Powell", {}).get("entries", [{}])[0]
        headline = rss.get("title", "Market quiet")

        payload = {
            "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
            "market_snapshot": { "SPY": {"price": spot, "change": -0.35, "vol": 1.2} },
            "headline": headline
        }
        return payload

    def invoke_vexy(self, payload: dict) -> dict:
        system_instruction = "You are a market color commentator. Given the structured data input, output a 2-sentence, high-energy summary suitable for a live ticker."
        prompt = f"{system_instruction}\n\nData: {json.dumps(payload, indent=2)}"
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            insight = response.choices[0].message.content.strip()
            if len(insight) < 20:
                insight = "Market update pending…"
        except Exception as e:
            insight = "Market update pending…"
            logger.error(f"Vexy invoke error: {e}")

        output = {
            "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
            "snapshot": payload.get("market_snapshot", {}),
            "insight": insight
        }
        return output

    def publish_commentary(self, output: dict):
        r.publish(self.pub_channel, json.dumps(output))
        logger.info(f"Vexy pub: {output['insight'][:50]}...")

    def scheduled_cycle(self):
        if datetime.now(ZoneInfo("UTC")).hour < 13 or datetime.now(ZoneInfo("UTC")).hour > 20:  # Trading hours UTC 13:30-20:00
            return
        payload = self.aggregate_data()
        output = self.invoke_vexy(payload)
        self.publish_commentary(output)

    def run(self):
        self.startup()
        self.scheduler.add_job(self.scheduled_cycle, 'interval', minutes=5)
        logger.info("🧠 Vexy AI running – 5-min cycles during trading hours")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.scheduler.shutdown()

if __name__ == "__main__":
    vexy = VexyWorkflow()
    vexy.run()