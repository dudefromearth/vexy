#!/bin/bash
# Vexy Startup Shell Script – Test Composed System
# Run: ./scripts/startup.sh

# Create scripts dir if missing
mkdir -p scripts

# Activate venv
source .venv/bin/activate

# Load Truth
python services/truth_loader.py

# Fetch content
python -m services.polygon_fetcher
python -m services.rss_loader

# Aggregate & Vexy workflow
python services/data_aggregator.py
python services/vexy_analysts.py
python services/vexy_publisher.py

# Probe pub
echo "Probing Redis pub..."
redis-cli monitor --duration 5

# Deactivate
deactivate