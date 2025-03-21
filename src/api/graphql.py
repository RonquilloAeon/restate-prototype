import hashlib
import json
import logging
import os
import time
import math

import httpx
import strawberry
from strawberry.scalars import JSON
from enum import Enum
from typing import Literal, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
RESTATE_ENDPOINT = os.getenv("RESTATE_ENDPOINT")


def generate_idempotency_key(service_name: str, handler_name: str, data: dict, time_window_seconds: Optional[int] = None) -> str:
    payload_str = json.dumps(data, sort_keys=True)
    
    # If time_window_seconds is specified, include a time bucket in the hash
    time_component = ""
    if time_window_seconds:
        # Create a time bucket based on the current time divided by the window
        current_time = math.floor(time.time())
        time_bucket = current_time // time_window_seconds
        time_component = f":{time_bucket}"
    
    str_to_hash = f"{service_name}:{handler_name}:{payload_str}:{time_component}"
    return hashlib.sha256(str_to_hash.encode()).hexdigest()


async def call_restate(service_or_workflow_name: str, handler_name: str, data: Optional[dict] = None, time_window_seconds: Optional[int] = None, call_type: Literal["send"] = None, include_idempotency_key: bool = True) -> str:
    endpoint = f"{RESTATE_ENDPOINT}/{service_or_workflow_name}/{handler_name}{f'/{call_type}' if call_type else ''}"
    
    # Use a 30-second idempotency window if not specified
    if handler_name == "toggle_lightbulb" and time_window_seconds is None:
        time_window_seconds = 20
    elif handler_name == "get_lightbulb" and time_window_seconds is None:
        time_window_seconds = 5
    else:
        time_window_seconds = 30

    key = generate_idempotency_key(service_or_workflow_name, handler_name, data or {}, time_window_seconds)
        
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if include_idempotency_key:
        headers["idempotency-key"] = key

    logger.info("Calling Restate service: %s, data: %s", endpoint, data)
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(endpoint, headers=headers, json=data)

            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # TODO HANDLE 409 - return message
        # TODO handle 500 - TerminalError
        logger.error(f"Error calling Restate service: {e}: {e.response.text}")

        raise e from None

    return key


async def get_restate_output(key: str, service_name: str, handler_name: str) -> dict:
    endpoint = f"{RESTATE_ENDPOINT}/restate/invocation/{service_name}/{handler_name}/{key}/output"

    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint)

        response.raise_for_status()
        return response.json()


@strawberry.enum
class LightStatus(Enum):
    ON = "on"
    OFF = "off"


@strawberry.input
class LightBulbInstallationInput:
    id: str
    data: Optional[JSON] = None


@strawberry.type
class LightBulb:
    id: str
    status: LightStatus
    

@strawberry.type
class ActionSuccess:
    key: str


@strawberry.type
class Query:
    @strawberry.field
    async def lightbulb(self, id: str) -> Optional[LightBulb]:
        try:
            key = await call_restate("LightbulbManagementSvc", "get_lightbulb", {"id": id})
            result = await get_restate_output(key, "LightbulbManagementSvc", "get_lightbulb")

            return LightBulb(id=result["id"], status=LightStatus[result["data"]["status"]])
        except Exception as e:
            logger.exception("Error fetching lightbulb status: %s", e)
            return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def install_lightbulb(self, input: LightBulbInstallationInput) -> Optional[ActionSuccess]:
        try:
            logger.info("Installing lightbulb with id: %s", input.id)
            key = await call_restate("InstallationWorkflow", input.id, call_type="run", data={"id": input.id, "data": input.data}, include_idempotency_key=False)
            return ActionSuccess(key=key)
        except Exception as e:
            logger.exception("Error installing lightbulb: %s", e)
            return None

    @strawberry.mutation
    async def toggle_lightbulb(self, id: str) -> Optional[ActionSuccess]:
        try:
            logger.info("Toggling lightbulb with id: %s", id)
            key = await call_restate("LightbulbManagementSvc", "toggle_lightbulb", {"id": id})
            return ActionSuccess(key=key)
        except Exception as e:
            logger.exception("Error toggling lightbulb: %s", e)
            return None
        
    @strawberry.mutation
    async def uninstall_lightbulb(self, id: str) -> Optional[ActionSuccess]:
        try:
            logger.info("Uninstalling lightbulb with id: %s", id)
            key = await call_restate("LightbulbManagementSvc", "uninstall_lightbulb", {"id": id})
            return ActionSuccess(key=key)
        except Exception as e:
            logger.exception("Error uninstalling lightbulb: %s", e)
            return None


schema = strawberry.Schema(query=Query, mutation=Mutation)
