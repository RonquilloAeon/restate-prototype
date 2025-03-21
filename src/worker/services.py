import logging
from typing import Annotated, AsyncGenerator

from nats.aio.client import Client as NATS
from nats.errors import NoRespondersError
from wireup import Inject, service

logger = logging.getLogger(__name__)


class NATSClient:
    def __init__(self, nats_url: str):
        self.nc = NATS()
        self.nats_url = nats_url

    async def connect(self):
        await self.nc.connect(self.nats_url)
        logger.info(f"Connected to NATS at {self.nats_url}")

    async def request(self, subject: str, data: str) -> str:
        logger.info("Sending request to subject: %s with data: %s", subject, data)

        try:
            response = await self.nc.request(subject, data.encode(), timeout=1)
        except NoRespondersError as e:
            logger.error(f"No responders for subject: {subject}")
            raise e from None

        return response.data.decode()


@service
async def nats_client_factory(nats_url: Annotated[str, Inject(param="nats_url")]) -> AsyncGenerator[NATSClient]:
    client = NATSClient(nats_url)
    await client.connect()
    
    logger.info("Yielding NATSClient")
    yield client

    await client.nc.drain()
