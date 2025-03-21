import json
import pytest
import pytest_asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock
from src.worker.lightbulb_workflow import run
from src.worker.lightbulb_service import install_lightbulb, get_lightbulb, toggle_lightbulb, uninstall_lightbulb
from src.worker.models import LightbulbDataIo
from src.worker.services import NATSClient
from src.worker.di import container

@pytest_asyncio.fixture
def mock_context():
    context = AsyncMock()
    # Make ctx.set return a regular MagicMock instead of a coroutine to avoid unawaited coroutine warnings
    context.set = MagicMock()
    return context

@pytest_asyncio.fixture
def mock_service_context():
    ctx = AsyncMock()
    # Configure the run method to handle both coroutines and regular functions
    async def mocked_run(description, func_call, max_attempts=None):
        if description == "getting random delay":
            return 1  # Special case for the delay
            
        # Check if the function is awaitable
        if callable(func_call):
            if inspect.iscoroutinefunction(func_call):
                return await func_call()
            else:
                return func_call()
        return func_call
    
    ctx.run.side_effect = mocked_run
    return ctx

@pytest_asyncio.fixture
def mock_input():
    return LightbulbDataIo(id="test_id", data={"status": "ON"})

@pytest.mark.asyncio
async def test_run(mock_context, mock_service_context, mock_input, mock_nats_client):
    # Create a mock client with responses for different subjects
    mock_client = mock_nats_client({
        "lightbulb.install": json.dumps({
            "id": "test_id", 
            "success": True,
            "data": {"status": "OFF"}
        }),
        "lightbulb.get": json.dumps({
            "id": "test_id", 
            "success": True,
            "data": {"status": "OFF"}
        }),
        "lightbulb.toggle": json.dumps({
            "id": "test_id", 
            "success": True,
            "data": {"status": "ON"}
        }),
        "lightbulb.uninstall": json.dumps({
            "id": "test_id", 
            "success": True
        })
    })
    
    # Override the service_call method to actually call the service functions
    async def mock_service_call(service_func, arg):
        if service_func == install_lightbulb:
            return await install_lightbulb(mock_service_context, arg)
        elif service_func == get_lightbulb:
            return await get_lightbulb(mock_service_context, arg)
        elif service_func == toggle_lightbulb:
            return await toggle_lightbulb(mock_service_context, arg)
        elif service_func == uninstall_lightbulb:
            return await uninstall_lightbulb(mock_service_context, arg)
    
    mock_context.service_call.side_effect = mock_service_call
    
    # Override the NATSClient in the container
    with container.override.service(target=NATSClient, new=mock_client):
        await run(mock_context, mock_input)
        
        # Verify context.set was called with the expected values
        assert mock_context.set.call_count == 4
        mock_context.set.assert_any_call("installation_status", "installed")
        mock_context.set.assert_any_call("installation_status", "status_fetched")
        mock_context.set.assert_any_call("installation_status", "toggled")
        mock_context.set.assert_any_call("installation_status", "completed")
        
        # Verify the NATS client was called with the correct subjects
        assert len(mock_client.calls) == 4
        assert mock_client.calls[0]["subject"] == "lightbulb.install"
        assert mock_client.calls[1]["subject"] == "lightbulb.get"
        assert mock_client.calls[2]["subject"] == "lightbulb.toggle"
        # The last call should be to toggle again to restore original state
        assert mock_client.calls[3]["subject"] == "lightbulb.toggle"
