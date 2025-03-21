import pytest_asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock

# Import after adjusting path
from src.worker.services import NATSClient

class MockNATSClient(NATSClient):
    """Mock implementation of NATSClient for testing"""
    
    def __init__(self, mock_responses: Dict[str, Any] = None):
        # Don't call parent init to avoid actual NATS connection
        self.mock_responses = mock_responses or {}
        self.nc = AsyncMock()
        self.calls = []
        
    async def connect(self):
        # Do nothing for connect - no real connection needed
        pass
        
    async def request(self, subject: str, data: str) -> str:
        """Mock implementation that returns pre-configured responses based on subject"""
        # Record the call for later verification
        self.calls.append({"subject": subject, "data": data})
        
        if subject in self.mock_responses:
            response = self.mock_responses[subject]
            if callable(response):
                # If the response is a function, call it with the data
                parsed_data = json.loads(data)
                return response(parsed_data)
            else:
                # Otherwise return the static response
                return response
        else:
            # Default response if no specific one is configured
            return json.dumps({"success": True, "id": json.loads(data).get("id"), "data": {"status": "MOCKED"}})

@pytest_asyncio.fixture
def mock_nats_client():
    """Fixture that provides a mock NATS client with configurable responses"""
    def _create_mock_client(responses=None):
        return MockNATSClient(responses)
    return _create_mock_client
