import logging
import random

from restate.exceptions import TerminalError

from src.models import LightbulbRequest, LightbulbResponse
from . import services
from .di import container

logger = logging.getLogger(__name__)


async def send_lightbulb_request(id: str, subject: str, data: dict | None = None) -> str:
    nats_client = await container.aget(services.NATSClient)
    request = LightbulbRequest(id=id, data=data)
    logger.info(f"Sending request for lightbulb {id} to subject {subject}: {request}")
    
    response = await nats_client.request(subject, request.model_dump_json())
    logger.info(f"Received response for lightbulb {id}: {response}")
    result = LightbulbResponse.model_validate_json(response)

    if not result.success:
        raise TerminalError(result.error_message)
    else:
        return response


def get_random_delay() -> int:
    return random.randint(1, 5)
