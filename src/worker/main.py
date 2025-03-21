import logging

import restate

from .di import container
from .lightbulb_service import lightbulb_service
from .lightbulb_workflow import installation_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    logger.info("Creating Restate app w/ lifespan")
    _restate_app = restate.app([installation_workflow, lightbulb_service])

    async def _app(scope, receive, send):
        if scope['type'] == 'lifespan':
            logger.info("Handling lifespan request")
            while True:
                message = await receive()

                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await container.aclose()
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        else:
            logger.info("Handling non-lifespan request")
            return await _restate_app(scope, receive, send)
        
    return _app


app = create_app()
