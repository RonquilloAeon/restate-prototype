import wireup

from . import services

container = wireup.create_container(
    parameters={
        "nats_url": "nats://nats:4222",
    },
    service_modules=[services]
)
