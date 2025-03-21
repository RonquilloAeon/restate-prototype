import asyncio
import logging
import random
import typing
from pydantic import ValidationError
from src.models import LightbulbRequest, LightbulbResponse

import nats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to track light bulb states
light_bulbs = {}


def return_validation_error_response(e: ValidationError) -> LightbulbResponse:
    return LightbulbResponse(success=False, error_message=str(e))


def construct_handler(nc: nats.aio.client.Client) -> typing.Coroutine:
    def _get_response(sub: str, data: str) -> LightbulbResponse:
        match sub:
            case "lightbulb.get":
                try:
                    request = LightbulbRequest.model_validate_json(data)
                except ValidationError as e:
                    response = return_validation_error_response(e)
                else:
                    if request.id not in light_bulbs:
                        light_bulbs[request.id] = random.choice(["ON", "OFF"])
                    response = LightbulbResponse(id=request.id, data={"status": light_bulbs[request.id]}, success=True)
            case "lightbulb.toggle":
                try:
                    request = LightbulbRequest.model_validate_json(data)
                except ValidationError as e:
                    response = return_validation_error_response(e)
                else:
                    if request.id not in light_bulbs:
                        light_bulbs[request.id] = random.choice(["ON", "OFF"])
                    else:
                        light_bulbs[request.id] = "OFF" if light_bulbs[request.id] == "ON" else "ON"
                    response = LightbulbResponse(id=request.id, data={"status": light_bulbs[request.id]}, success=True)
            case _:
                response = LightbulbResponse(success=False, error_message="Unknown subject")

        return response

    async def _handler(msg):
        subject = msg.subject
        reply = msg.reply
        recv_data = msg.data.decode()
        logger.info(f"Received a message on '{subject} {reply}': {recv_data}")

        try:
            response = _get_response(subject, recv_data)
        except Exception as e:
            logger.error(f"Unhandled processing error: {e}")
            response = LightbulbResponse(success=False, error_message="We encountered an unexpected error")

        reply_data = response.model_dump_json().encode()
        logger.info(f"Sending response: {reply_data}")

        await nc.publish(reply, reply_data)

    return _handler


async def main():
    nc = await nats.connect("nats://nats:4222")
    message_handler = construct_handler(nc)

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
