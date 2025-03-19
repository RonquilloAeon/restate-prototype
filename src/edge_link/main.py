import asyncio
import logging
import random

import nats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to track light bulb states
light_bulbs = {}

async def main():
    nc = await nats.connect("nats://nats:4222")

    async def message_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        logger.info(f"Received a message on '{subject} {reply}': {data}")

        if subject == "lightbulb.get":
            bulb_id = data
            if bulb_id not in light_bulbs:
                light_bulbs[bulb_id] = random.choice(["ON", "OFF"])
            await nc.publish(reply, light_bulbs[bulb_id].encode())

        elif subject == "lightbulb.toggle":
            bulb_id = data
            if bulb_id not in light_bulbs:
                light_bulbs[bulb_id] = random.choice(["ON", "OFF"])
            else:
                light_bulbs[bulb_id] = "OFF" if light_bulbs[bulb_id] == "ON" else "ON"
            await nc.publish(reply, light_bulbs[bulb_id].encode())

    await nc.subscribe("lightbulb.get", cb=message_handler)
    await nc.subscribe("lightbulb.toggle", cb=message_handler)

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Shutting down NATS edge link simulator")
        await nc.drain()


if __name__ == '__main__':
    logger.info("Starting NATS edge link simulator")
    asyncio.run(main())
