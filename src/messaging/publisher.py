import json
import pika

from datetime import datetime, timezone
from uuid import uuid4
from src.messaging.config import EVENT_EXCHANGE, SEASON_COLLECTED_ROUTING_KEY
from src.messaging.connection import create_connection
from src.messaging.topology import declare_analysis_topology

# publish event after season data has been collected / committed
def publish_season_collected(season: str, players: int, inserted: int, updated: int) -> dict:
    # create event structure
    event = {
        "event_id": str(uuid4()),
        "event_type": "season_data_collected",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": {
            "season": season,
            "players": players,
            "inserted": inserted,
            "updated": updated
        }
    }
    
    connection = None
    try: 
        # create RabbitMQ connection
        connection = create_connection()
        channel = connection.channel()
        declare_analysis_topology(channel)
        
        # publish event message
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=EVENT_EXCHANGE,
            routing_key=SEASON_COLLECTED_ROUTING_KEY,
            body=json.dumps(event),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent, message_id=event["event_id"], type=event["event_type"]),
            mandatory=True
        )
        
        # failed publish error check
        # if not published:
        #     raise RuntimeError("Failed RabbitMQ published event for collecting season data")

        return event
    
    except pika.exceptions.UnroutableError:
        raise RuntimeError("RabbitMQ could not route the season-collected event")

    except pika.exceptions.NackError:
        raise RuntimeError("RabbitMQ rejected the season-collected event")

    except pika.exceptions.AMQPError:
        raise RuntimeError("RabbitMQ failed while publishing the season-collected event")
    
    finally:
        if connection is not None and connection.is_open:
            connection.close()
