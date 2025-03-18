from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional


class LightStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"


class LightBulb(BaseModel):
    id: str
    location: str
    status: LightStatus = LightStatus.OFF


class Location(BaseModel):
    name: str
    light_ids: List[str] = []