import json
import redis
from services.truth_loader import TruthLoader

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class VexyConfig:
    def __init__(self):
        loader = TruthLoader(r)
        schema = loader.load_schema()
        self.name = schema["vexy"]["name"]
        self.identity = schema["vexy"]["identity"]
        self.config = schema["vexy"]["config"]
        self.assistant_id = self.config["assistant_id"]

    def get_prompt_template(self, template_name: str) -> str:
        return self.config["prompt_templates"][template_name].format(data="{}")  # Placeholder for data

# Test
if __name__ == "__main__":
    config = VexyConfig()
    print(f"Vexy loaded: {config.name} as {config.identity}")
    print(f"Config: {config.config}")
    print(f"Assistant ID: {config.assistant_id}")
    print(f"Prompt template: {config.get_prompt_template('commentary')}")