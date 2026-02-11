
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.crawler.live_sync_service import app, AppState

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch("src.crawler.live_sync_service.state") as mock_state:
        # Mock ChromaDB
        mock_state.chroma_client = MagicMock()
        mock_state.collection = MagicMock()
        
        # Mock SentenceTransformer
        mock_state.model = MagicMock()
        # model.encode returns a numpy array which has .tolist()
        # We mock the return value object to have a tolist method
        mock_array = MagicMock()
        mock_array.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_state.model.encode.return_value = mock_array
        
        # Mock HTTP Client
        mock_state.http_client = AsyncMock()
        
        yield mock_state

@patch("src.crawler.live_sync_service.process_page")
def test_sync_endpoint_success(mock_process_page, mock_dependencies):
    # Setup mock return from crawler
    mock_process_page.return_value = [
        {
            "text": "Test Content",
            "source": "/content/test",
            "chunk_id": 0,
            "metadata": {"title": "Test Page"}
        }
    ]
    
    response = client.post(
        "/api/v1/sync",
        json={"path": "/content/test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_processed"] == 1
    assert data["chunks_upserted"] == 1
    
    # Verify upsert called
    mock_dependencies.collection.upsert.assert_called_once()


@patch("src.crawler.live_sync_service.process_page")
def test_sync_endpoint_no_content(mock_process_page, mock_dependencies):
    # Setup empty mock return
    mock_process_page.return_value = []
    
    response = client.post(
        "/api/v1/sync",
        json={"path": "/content/test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_processed"] == 0

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_invalid_path():
    response = client.post(
        "/api/v1/sync",
        json={"path": "/invalid/path"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
