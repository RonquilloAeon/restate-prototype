import strawberry
from enum import Enum
from typing import List, Optional

from lightbulbs.models import LightStatus as ModelLightStatus
from lightbulbs.models import LightBulb as ModelLightBulb
from lightbulbs.models import Location as ModelLocation
from lightbulbs.service import lightbulb_service, location_service


@strawberry.enum
class LightStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"


@strawberry.type
class LightBulb:
    id: str
    location: str
    status: LightStatus

    @classmethod
    def from_model(cls, model: ModelLightBulb) -> "LightBulb":
        return cls(
            id=model.id,
            location=model.location,
            status=LightStatus.ON if model.status == ModelLightStatus.ON else LightStatus.OFF
        )


@strawberry.type
class Location:
    name: str
    light_ids: List[str]

    @classmethod
    def from_model(cls, model: ModelLocation) -> "Location":
        return cls(
            name=model.name,
            light_ids=model.light_ids
        )


@strawberry.type
class Query:
    @strawberry.field
    async def lightbulb(self, id: str) -> Optional[LightBulb]:
        try:
            bulb = await lightbulb_service.get_lightbulb(id)
            return LightBulb.from_model(bulb)
        except Exception:
            return None

    @strawberry.field
    async def location(self, name: str) -> Optional[Location]:
        try:
            loc = await location_service.get_location(name)
            return Location.from_model(loc)
        except Exception:
            return None

    @strawberry.field
    async def location_lightbulbs(self, location_name: str) -> List[LightBulb]:
        try:
            bulbs = await location_service.get_lights_in_location(location_name)
            return [LightBulb.from_model(bulb) for bulb in bulbs]
        except Exception:
            return []


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def register_lightbulb(self, id: str, location: str, status: LightStatus = LightStatus.OFF) -> LightBulb:
        model_status = ModelLightStatus.ON if status == LightStatus.ON else ModelLightStatus.OFF
        bulb = ModelLightBulb(id=id, location=location, status=model_status)
        result = await lightbulb_service.register_lightbulb(id, bulb)
        return LightBulb.from_model(result)

    @strawberry.mutation
    async def toggle_lightbulb(self, id: str) -> Optional[LightBulb]:
        try:
            result = await lightbulb_service.toggle_lightbulb(id)
            return LightBulb.from_model(result)
        except Exception:
            return None


schema = strawberry.Schema(query=Query, mutation=Mutation)