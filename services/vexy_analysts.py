import openai
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

openai.api_key = os.getenv("OPENAI_KEY")

def invoke_vexy_analysts(snapshot: dict) -> dict:
    system_instruction = "You are a market color commentator. Given the structured data input, output a 2-sentence, high-energy summary suitable for a live ticker."
    prompt = f"{system_instruction}\n\nData: {json.dumps(snapshot, indent=2)}"
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
        print(f"Vexy Analysts error: {e}")

    output = {
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
        "snapshot": snapshot["market_snapshot"],
        "insight": insight
    }
    return output

# Test
if __name__ == "__main__":
    sample_snapshot = {"timestamp": "2025-10-28T14:00:00Z", "market_snapshot": {"SPY": {"price": 523.45, "change": -0.35}}, "headline": "Bond yields up"}
    output = invoke_vexy_analysts(sample_snapshot)
    print("Vexy Analysts output:", json.dumps(output, indent=2))