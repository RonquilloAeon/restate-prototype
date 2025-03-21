import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from src.worker.lightbulb_service import install_lightbulb, get_lightbulb, toggle_lightbulb, uninstall_lightbulb
from src.worker.models import LightbulbIdInput, LightbulbDataIo
from src.worker.services import NATSClient
from src.worker.di import container

@pytest_asyncio.fixture
def mock_context():
    ctx = AsyncMock()
    # Configure the run method to forward its second argument's result
    async def mocked_run(description, func_call, max_attempts=None):
        # Just call the function that was wrapped by wrap_async_call
        if callable(func_call):
            return await func_call()
        return func_call
    
    ctx.run.side_effect = mocked_run
    return ctx

@pytest_asyncio.fixture
def mock_input():
    return LightbulbDataIo(id="test_id", data={"status": "ON"})

@pytest_asyncio.fixture
def mock_id_input():
    return LightbulbIdInput(id="test_id")

@pytest.mark.asyncio
async def test_install_lightbulb(mock_context, mock_input, mock_nats_client):
    # Create a mock NATS client with specific response for the install subject
    mock_client = mock_nats_client({
        "lightbulb.install": json.dumps({
            "id": "test_id", 
            "success": True, 
            "status": "installed"
        })
    })
    
    # Use Wireup's override functionality to inject our mock client
    with container.override.service(target=NATSClient, new=mock_client):
        response = await install_lightbulb(mock_context, mock_input)
        
        # Verify the response
        assert response.id == "test_id"
        assert response.success is True
        
        # Verify the client was called with the correct subject
        assert len(mock_client.calls) == 1
        assert mock_client.calls[0]["subject"] == "lightbulb.install"
        
        # Parse the request data to verify it contains the expected ID
        request_data = json.loads(mock_client.calls[0]["data"])
        assert request_data["id"] == "test_id"

@pytest.mark.asyncio
async def test_get_lightbulb(mock_context, mock_id_input, mock_nats_client):
    mock_client = mock_nats_client({
        "lightbulb.get": json.dumps({
            "id": "test_id", 
            "success": True, 
            "status": "ON",
            "data": {"status": "ON"}
        })
    })
    
    with container.override.service(target=NATSClient, new=mock_client):
        response = await get_lightbulb(mock_context, mock_id_input)
        
        assert response.id == "test_id"
        assert response.success is True
        
        assert len(mock_client.calls) == 1
        assert mock_client.calls[0]["subject"] == "lightbulb.get"
        
        request_data = json.loads(mock_client.calls[0]["data"])
        assert request_data["id"] == "test_id"

@pytest.mark.asyncio
async def test_toggle_lightbulb(mock_context, mock_id_input, mock_nats_client):
    mock_client = mock_nats_client({
        "lightbulb.toggle": json.dumps({
            "id": "test_id", 
            "success": True,
            "data": {"status": "OFF"}
        })
    })
    
    # Need to handle both the send_lightbulb_request and the get_random_delay calls
    async def mocked_run(description, func_call, max_attempts=None):
        if description == "getting random delay":
            return 1
        # Otherwise, call the function
        if callable(func_call):
            return await func_call()
        return func_call
    
    mock_context.run.side_effect = mocked_run
    
    with container.override.service(target=NATSClient, new=mock_client):
        response = await toggle_lightbulb(mock_context, mock_id_input)
        
        assert response.id == "test_id"
        assert response.data["status"] == "OFF"
        assert response.run_time == 1
        
        assert len(mock_client.calls) == 1
        assert mock_client.calls[0]["subject"] == "lightbulb.toggle"

@pytest.mark.asyncio
async def test_uninstall_lightbulb(mock_context, mock_id_input, mock_nats_client):
    mock_client = mock_nats_client({
        "lightbulb.uninstall": json.dumps({
            "id": "test_id", 
            "success": True
        })
    })
    
    with container.override.service(target=NATSClient, new=mock_client):
        response = await uninstall_lightbulb(mock_context, mock_id_input)
        
        assert response is True
        
        assert len(mock_client.calls) == 1
        assert mock_client.calls[0]["subject"] == "lightbulb.uninstall"
