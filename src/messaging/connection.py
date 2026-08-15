import pika

from src.messaging.config import RABBITMQ_URL

# Create RabbitMQ connection
def create_connection() -> pika.BlockingConnection:
    params = pika.URLParameters(RABBITMQ_URL)
    # detect broken connections
    params.heartbeat = 60
    params.blocked_connection_timeout = 30
    
    return pika.BlockingConnection(params)
