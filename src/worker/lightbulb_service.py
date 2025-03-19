import asyncio
import random

from pydantic import BaseModel
from restate import Service, Context
from restate.exceptions import TerminalError

from src.models import LightBulb, LightStatus
from . import services
from .di import container

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
    return await nats_client.request("lightbulb.get", id)


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
    return await nats_client.request("lightbulb.toggle", id)


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
