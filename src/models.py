from enum import Enum
from pydantic import BaseModel


class LightStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"


class LightBulb(BaseModel):
    id: str
    status: LightStatus = LightStatus.OFF
