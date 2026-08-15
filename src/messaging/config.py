import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")

EVENT_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "careerlens.events")

ANALYSIS_QUEUE = os.getenv("RABBITMQ_ANALYSIS_QUEUE", "season-analysis")

SEASON_COLLECTED_ROUTING_KEY = "season.data.collected"