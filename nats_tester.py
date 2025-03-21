import asyncio
import nats
import logging

from src.models import LightbulbRequest, LightbulbResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_nats():
    nc = await nats.connect("nats://localhost:4222")

    async def request_lightbulb_state(bulb_id):
        request = LightbulbRequest(id=bulb_id)
        response = await nc.request("lightbulb.get", request.model_dump_json().encode(), timeout=1)
        logger.info(f"Lightbulb {bulb_id} state: {response.data.decode()}")

    async def toggle_lightbulb(bulb_id):
        request = LightbulbRequest(id=bulb_id)
        response = await nc.request("lightbulb.toggle", request.model_dump_json().encode(), timeout=1)
        logger.info(f"Lightbulb {bulb_id} toggled to: {response.data.decode()}")

    bulb_id = "bulb-1"
    await request_lightbulb_state(bulb_id)
    await toggle_lightbulb(bulb_id)
    await request_lightbulb_state(bulb_id)
    await toggle_lightbulb(bulb_id)
    await request_lightbulb_state(bulb_id)
    await request_lightbulb_state(bulb_id)

    await nc.drain()

if __name__ == '__main__':
    asyncio.run(test_nats())
