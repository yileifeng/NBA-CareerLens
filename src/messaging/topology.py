import pika
from src.messaging.config import ANALYSIS_QUEUE, EVENT_EXCHANGE, SEASON_COLLECTED_ROUTING_KEY

# declare exchange, queue and binding for analysis events
def declare_analysis_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
   channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="direct", durable=True)
   channel.queue_declare(queue=ANALYSIS_QUEUE, durable=True)
   channel.queue_bind(exchange=EVENT_EXCHANGE, queue=ANALYSIS_QUEUE, routing_key=SEASON_COLLECTED_ROUTING_KEY)
 