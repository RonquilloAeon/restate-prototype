import asyncio

from restate import Service, Context
from restate.exceptions import TerminalError

from .models import LightbulbIdInput, LightbulbDataIo, ToggleLightbulbResponse
from .utils import send_lightbulb_request, get_random_delay
from src.models import LightbulbResponse, ToggleLightbulbResponse

lightbulb_service = Service("LightbulbManagementSvc")


def wrap_async_call(coro_fn, *args, **kwargs):
    async def wrapped():
        return await coro_fn(*args, **kwargs)

    return wrapped


@lightbulb_service.handler()
async def install_lightbulb(ctx: Context, input_: LightbulbDataIo) -> LightbulbResponse:
    """Install a new light bulb by its ID"""

    try:
        result = await ctx.run("installing new lightbulb", wrap_async_call(send_lightbulb_request, input_.id, "lightbulb.install", input_.data), max_attempts=5)
    except TerminalError as e:
        raise e
    
    return LightbulbResponse.model_validate_json(result)


@lightbulb_service.handler()
async def get_lightbulb(ctx: Context, input_: LightbulbIdInput) -> LightbulbResponse:
    """Get a light bulb by its ID"""

    try:
        result = await ctx.run("fetching lightbulb status", wrap_async_call(send_lightbulb_request, input_.id, "lightbulb.get"), max_attempts=3)
    except TerminalError as e:
        # TODO ensure returned error message is useful
        raise e

    return LightbulbResponse.model_validate_json(result)


@lightbulb_service.handler()
async def toggle_lightbulb(ctx: Context, input_: LightbulbIdInput) -> ToggleLightbulbResponse:
    """Toggle a light bulb's status between ON and OFF"""

    try:
        result = await ctx.run("toggling lightbulb status", wrap_async_call(send_lightbulb_request, input_.id, "lightbulb.toggle"), max_attempts=3)
    except TerminalError as e:
        raise e
    
    # Simulate some delay for toggling
    delay = await ctx.run("getting random delay", lambda: get_random_delay(), max_attempts=3)
    await asyncio.sleep(delay)

    result = LightbulbResponse.model_validate_json(result)

    return ToggleLightbulbResponse(id=result.id, data=result.data, run_time=delay)


@lightbulb_service.handler()
async def uninstall_lightbulb(ctx: Context, input_: LightbulbIdInput) -> bool:
    """Install a new light bulb by its ID"""

    try:
        result = await ctx.run("uninstalling lightbulb", wrap_async_call(send_lightbulb_request, input_.id, "lightbulb.uninstall"), max_attempts=5)
    except TerminalError as e:
        raise e
    
    result = LightbulbResponse.model_validate_json(result)

    return result.success
