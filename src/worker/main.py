import logging

import restate

from .service import lightbulb_service


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting Restate app")
app = restate.app([lightbulb_service])
