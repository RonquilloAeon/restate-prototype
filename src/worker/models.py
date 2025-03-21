from pydantic import BaseModel


class LightbulbIdInput(BaseModel):
    id: str


class LightbulbDataIo(LightbulbIdInput):
    data: dict | None = None


class ToggleLightbulbResponse(LightbulbDataIo):
    run_time: int
