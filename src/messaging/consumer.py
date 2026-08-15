import json
import logging
import pika

from src.app import create_app
from src.messaging.config import ANALYSIS_QUEUE
from src.messaging.connection import create_connection
from src.messaging.topology import declare_analysis_topology
from src.services.event_processor import process_season_collected

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

# process RabbitMQ analysis event
def handle_message(channel, method, properties, body) -> None:
    try:
        event = json.loads(body.decode("utf-8"))
        logger.info("Received event %s", event.get("event_id"))
        
        # SQLAlchemy and Flask config
        with app.app_context():
            res = process_season_collected(event)
        
        logger.info("Processed season %s with %s players", res["season"], res["players"])
        
        # ack successful process
        channel.basic_ack(delivery_tag=method.delivery_tag)
        
    except ValueError:
        logger.exception("Invalid event")
        # reject failed process
        channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        
# start consuming analysis event
def run_consumer() -> None:
    connection = create_connection()
    channel = connection.channel()
    declare_analysis_topology(channel)
    
    # limit to 1 message unacknowledged
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=ANALYSIS_QUEUE, on_message_callback=handle_message, auto_ack=False)
    
    logger.info("Waiting for messages on queue...")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping consumer process...")
        channel.stop_consuming()
    finally:
        if connection.is_open:
            connection.close()
            
if __name__ == "__main__":
    run_consumer()
