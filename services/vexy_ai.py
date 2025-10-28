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
logger = logging.getLogger("VexyAI")

class VexyAI:
    def __init__(self):
        self.sub_data = {}  # Accumulated from sub
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.pub_channel = "truth:vexy:commentary"

    def startup(self):
        logger.info("🧠 Vexy AI startup – subbing Redis for data")
        pubsub = r.pubsub()
        pubsub.subscribe("truth:chain:raw:*", "truth:feed:rss:*")
        for message in pubsub.listen():
            if message['type'] == 'message':
                event = json.loads(message['data'])
                channel = message['channel']
                self.sub_data[channel] = event
                logger.info(f"Vexy sub: {channel} – {event.get('symbol', event.get('title', 'Data'))}")

    def aggregate_prompt(self) -> dict:
        chain = self.sub_data.get("truth:chain:raw:SPY", {})
        spot = chain.get("spot_price", 523.45)
        rss = self.sub_data.get("truth:feed:rss:Jerome Powell", {}).get("entries", [{}])[0]
        headline = rss.get("title", "Market quiet")
        return {
            "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
            "market_snapshot": {"SPY": {"price": spot, "change": -0.35, "vol": 1.2}},
            "headline": headline
        }

    def scheduled_invoke(self):
        payload = self.aggregate_prompt()
        system_instruction = "You are a market color commentator. Given the structured data input, output a 2-sentence, high-energy summary suitable for a live ticker."
        prompt = f"{system_instruction}\n\nData: {json.dumps(payload, indent=2)}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
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
            "snapshot": payload["market_snapshot"],
            "insight": insight
        }
        r.publish(self.pub_channel, json.dumps(output))
        logger.info(f"Vexy scheduled: {insight[:50]}...")

    def run(self):
        self.startup()
        self.scheduler.add_job(self.scheduled_invoke, 'interval', minutes=5)
        logger.info("🧠 Vexy AI running – 5-min prompts from Redis data")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.scheduler.shutdown()