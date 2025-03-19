import asyncio
import random
import logging

from pydantic import BaseModel
from restate import Service, Context

from src.models import LightBulb, LightStatus
from . import services
from .di import container

logger = logging.getLogger(__name__)

lightbulb_service = Service("lightbulb_manager")


class LightbulbInput(BaseModel):
    id: str


class ToggleLightbulbInput(LightbulbInput):
    status: LightStatus


class ToggleLightbulbResponse(ToggleLightbulbInput):
    run_time: int

@lightbulb_service.handler()
async def get_lightbulb(ctx: Context, data: LightbulbInput) -> LightBulb:
    """Get a light bulb by its ID"""
    nats_client = await container.aget(services.NATSClient)
    await asyncio.sleep(random.randint(1, 2))  # Simulate some delay

    status = await nats_client.request("lightbulb.get", data.id)
    logger.info(f"Light bulb status for ID {data.id}: {status}")

    return LightBulb(id=data.id, status=LightStatus(status))


@lightbulb_service.handler()
async def toggle_lightbulb(ctx: Context, data: ToggleLightbulbInput) -> ToggleLightbulbResponse:
    """Toggle a light bulb's status between ON and OFF"""
    nats_client = await container.aget(services.NATSClient)
    delay = random.randint(1, 2)
    await asyncio.sleep(delay)  # Simulate some delay

    status = await nats_client.request("lightbulb.toggle", data.id)
    logger.info(f"Toggled light bulb {data.id} to status: {status}")

    return ToggleLightbulbResponse(id=data.id, status=LightStatus(status), run_time=delay)
