import asyncio
from random import choice, randint

from pydantic import BaseModel
from restate import Service, Context

from src.models import LightBulb, LightStatus

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
    await asyncio.sleep(randint(1, 3))  # Simulate some delay
    return LightBulb(
        id=data.id,
        status=choice([LightStatus.ON, LightStatus.OFF]),
    )


@lightbulb_service.handler()
async def toggle_lightbulb(ctx: Context, data: ToggleLightbulbInput) -> ToggleLightbulbResponse:
    """Toggle a light bulb's status between ON and OFF"""
    delay = randint(1, 4)
    await asyncio.sleep(delay)  # Simulate some delay
    
    return ToggleLightbulbResponse(id=data.id, status=data.status, run_time=delay)

