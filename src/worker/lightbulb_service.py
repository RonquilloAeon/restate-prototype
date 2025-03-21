import asyncio
import logging
import random

from pydantic import BaseModel
from restate import Service, Context
from restate.exceptions import TerminalError

from src.models import LightBulb, LightStatus, LightbulbRequest, LightbulbResponse, ToggleLightbulbResponse
from . import services
from .di import container

logger = logging.getLogger(__name__)

lightbulb_service = Service("lightbulb_manager")


class LightbulbInput(BaseModel):
    id: str


class ToggleLightbulbResponse(LightbulbInput):
    run_time: int


def wrap_async_call(coro_fn, *args, **kwargs):
    async def wrapped():
        return await coro_fn(*args, **kwargs)

    return wrapped


async def get_lightbulb_status(id: str) -> str:
    nats_client = await container.aget(services.NATSClient)
    request = LightbulbRequest(id=id)
    response = await nats_client.request("lightbulb.get", request.model_dump_json())
    logger.info(f"Received response for lightbulb {id}: {response}")

    return LightbulbResponse.model_validate_json(response).data["status"]


@lightbulb_service.handler()
async def get_lightbulb(ctx: Context, data: LightbulbInput) -> LightBulb:
    """Get a light bulb by its ID"""

    try:
        status = await ctx.run("fetching lightbulb status", wrap_async_call(get_lightbulb_status, data.id), max_attempts=3)
    except TerminalError as e:
        raise e

    return LightBulb(id=data.id, status=LightStatus(status))


async def change_lightbulb_status(id: str) -> str:
    nats_client = await container.aget(services.NATSClient)
    request = LightbulbRequest(id=id)
    response = await nats_client.request("lightbulb.toggle", request.model_dump_json())
    logger.info(f"Received response for toggling lightbulb {id}: {response}")

    return LightbulbResponse.model_validate_json(response).data["status"]


def get_random_delay() -> int:
    return random.randint(1, 5)


@lightbulb_service.handler()
async def toggle_lightbulb(ctx: Context, data: LightbulbInput) -> ToggleLightbulbResponse:
    """Toggle a light bulb's status between ON and OFF"""

    try:
        status = await ctx.run("toggling lightbulb status", wrap_async_call(change_lightbulb_status, data.id), max_attempts=3)
    except TerminalError as e:
        raise e
    
    # Simulate some delay for toggling
    delay = await ctx.run("getting random delay", lambda: get_random_delay(), max_attempts=3)
    await asyncio.sleep(delay)

    return ToggleLightbulbResponse(id=data.id, status=LightStatus(status), run_time=delay)
