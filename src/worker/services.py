from typing import Annotated, AsyncGenerator

from nats.aio.client import Client as NATS
from wireup import Inject, service



class NATSClient:
    def __init__(self, nats_url: str):
        self.nc = NATS()
        self.nats_url = nats_url

    async def connect(self):
        await self.nc.connect(self.nats_url)

    async def request(self, subject, data):
        response = await self.nc.request(subject, data.encode())
        return response.data.decode()


@service
async def nats_client_factory(nats_url: Annotated[str, Inject(param="nats_url")]) -> AsyncGenerator[NATSClient]:
    client = NATSClient(nats_url)
    await client.connect()
    
    yield client

    await client.nc.drain()
