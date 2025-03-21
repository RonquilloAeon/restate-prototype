from enum import Enum
from pydantic import BaseModel


class LightStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"


class LightBulb(BaseModel):
    id: str
    data: dict
    status: LightStatus = LightStatus.OFF


class LightbulbRequest(BaseModel):
    id: str
    data: dict | None = None

class LightbulbResponse(BaseModel):
    success: bool

    id: str | None = None
    data: dict | None = None
    error_message: str | None = None

class ToggleLightbulbResponse(LightbulbRequest):
    run_time: int
