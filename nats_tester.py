import argparse
import asyncio
import nats
import logging

from src.models import LightbulbRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_nats(bulb_id):
    nc = await nats.connect("nats://localhost:4222")

    async def request_lightbulb_state(bulb_id):
        request = LightbulbRequest(id=bulb_id)
        response = await nc.request("lightbulb.get", request.model_dump_json().encode(), timeout=1)
        logger.info(f"Lightbulb {bulb_id} state: {response.data.decode()}")

    async def toggle_lightbulb(bulb_id):
        request = LightbulbRequest(id=bulb_id)
        response = await nc.request("lightbulb.toggle", request.model_dump_json().encode(), timeout=1)
        logger.info(f"Lightbulb {bulb_id} toggled to: {response.data.decode()}")

    await request_lightbulb_state(bulb_id)
    await toggle_lightbulb(bulb_id)
    await request_lightbulb_state(bulb_id)

    await nc.drain()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test NATS with a specific lightbulb ID')
    parser.add_argument('bulb_id', type=str, help='The ID of the lightbulb to test')
    args = parser.parse_args()
    asyncio.run(test_nats(args.bulb_id))
