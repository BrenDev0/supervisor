import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, call
from uuid import UUID, uuid4
import httpx
from fastapi import WebSocket

from src.workflow.orchestrator.orchestrator import Orchestrator
from src.workflow.state import State
from src.workflow.agents.supervisor.supervisor_models import SupervisorOutput
from src.api.modules.interactions.interactions_models import WorkerState
from src.api.modules.websocket.websocket_service import WebsocketService


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing"""
    websocket = Mock(spec=WebSocket)
    websocket.send_json = AsyncMock()
    return websocket


@pytest.fixture
def mock_websocket_service(mock_websocket):
    """Mock WebSocketService for testing"""
    service = Mock(spec=WebsocketService)
    service.get_connection = Mock(return_value=mock_websocket)
    return service


@pytest.fixture
def orchestrator(mock_websocket_service):
    """Create Orchestrator instance with mocked websocket service"""
    return Orchestrator(mock_websocket_service)


@pytest.fixture
def mock_worker_state():
    """Mock WorkerState for testing"""
    return WorkerState(
        input="Can I terminate an employee without notice?",
        agents=[UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[
            {"role": "human", "content": "Previous question"},
            {"role": "ai", "content": "Previous answer"}
        ],
        user_id=uuid4()
    )


@pytest.fixture
def sample_state():
    """Sample state for testing orchestrator"""
    agent_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    chat_id = uuid4()
    
    return {
        "input": "Can I terminate an employee without notice?",
        "chat_id": chat_id,
        "available_agents": [agent_id],
        "selected_agents": SupervisorOutput({agent_id: True})
    }


# Unit Tests for Constructor

def test_orchestrator_constructor_initializes_websocket_service(mock_websocket_service):
    """Test that Orchestrator constructor properly initializes websocket service"""
    # Act
    orchestrator = Orchestrator(mock_websocket_service)
    
    # Assert
    assert orchestrator._Orchestrator__websocket_service == mock_websocket_service


def test_orchestrator_constructor_accepts_websocket_service_type():
    """Test that Orchestrator constructor accepts WebsocketService type"""
    # Arrange
    websocket_service = Mock(spec=WebsocketService)
    
    # Act & Assert - Should not raise any exceptions
    orchestrator = Orchestrator(websocket_service)
    assert orchestrator is not None


# Unit Tests for Agent Selection Logic

@pytest.mark.asyncio
async def test_orchestrate_filters_selected_and_available_agents(orchestrator, mock_worker_state):
    """Test that orchestrate only processes agents that are both selected and available"""
    # Arrange
    agent1_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    agent2_id = uuid4()
    agent3_id = uuid4()
    
    state = {
        "input": "Test question",
        "chat_id": uuid4(),
        "available_agents": [agent1_id, agent2_id],  # Only 1 and 2 are available
        "selected_agents": SupervisorOutput({
            agent1_id: True,   # Selected and available - should process
            agent2_id: False,  # Not selected - should not process
            agent3_id: True    # Selected but not available - should not process
        })
    }
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock) as mock_handle:
        # Act
        result = await orchestrator.orchestrate(state, mock_worker_state)
        
        # Assert
        # Should only call __handle_agent_interaction for agent1 (as string)
        mock_handle.assert_called_once()
        call_args = mock_handle.call_args
        assert call_args[1]["agent_id"] == str(agent1_id)


@pytest.mark.asyncio
async def test_orchestrate_handles_no_selected_agents(orchestrator, mock_worker_state):
    """Test that orchestrate handles case where no agents are selected"""
    # Arrange
    agent_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    
    state = {
        "input": "Test question",
        "chat_id": uuid4(),
        "available_agents": [agent_id],
        "selected_agents": SupervisorOutput({agent_id: False})  # No agents selected
    }
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock) as mock_handle:
        # Act
        result = await orchestrator.orchestrate(state, mock_worker_state)
        
        # Assert
        # Should not call __handle_agent_interaction
        mock_handle.assert_not_called()
        
        # Should still send empty agent list to frontend
        websocket = orchestrator._Orchestrator__websocket_service.get_connection.return_value
        websocket.send_json.assert_called_once_with({"agents": []})


@pytest.mark.asyncio
async def test_orchestrate_converts_agent_ids_to_strings(orchestrator, mock_worker_state):
    """Test that orchestrate converts UUID agent IDs to strings for JSON serialization"""
    # Arrange
    agent_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    
    state = {
        "input": "Test question",
        "chat_id": uuid4(),
        "available_agents": [agent_id],
        "selected_agents": SupervisorOutput({agent_id: True})
    }
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock) as mock_handle:
        # Act
        result = await orchestrator.orchestrate(state, mock_worker_state)
        
        # Assert
        # Check that string conversion happened in frontend message
        websocket = orchestrator._Orchestrator__websocket_service.get_connection.return_value
        websocket.send_json.assert_any_call({"agents": [str(agent_id)]})
        
        # Check that string was passed to handler
        call_args = mock_handle.call_args
        assert call_args[1]["agent_id"] == str(agent_id)
        assert isinstance(call_args[1]["agent_id"], str)


# Unit Tests for WebSocket Integration

@pytest.mark.asyncio
async def test_orchestrate_gets_websocket_connection_by_chat_id(orchestrator, mock_worker_state, sample_state):
    """Test that orchestrate gets websocket connection using chat_id"""
    # Arrange
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock):
        # Act
        await orchestrator.orchestrate(sample_state, mock_worker_state)
        
        # Assert - Now uses UUID directly, not string
        orchestrator._Orchestrator__websocket_service.get_connection.assert_called_once_with(sample_state["chat_id"])


@pytest.mark.asyncio
async def test_orchestrate_sends_agent_list_to_frontend(orchestrator, mock_worker_state, sample_state):
    """Test that orchestrate sends agent list to frontend via websocket"""
    # Arrange
    agent_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock):
        # Act
        await orchestrator.orchestrate(sample_state, mock_worker_state)
        
        # Assert
        websocket = orchestrator._Orchestrator__websocket_service.get_connection.return_value
        websocket.send_json.assert_any_call({"agents": [str(agent_id)]})


# Unit Tests for Parallel Processing

@pytest.mark.asyncio
async def test_orchestrate_handles_multiple_agents_in_parallel(orchestrator, mock_worker_state):
    """Test that orchestrate handles multiple agents in parallel using asyncio.gather"""
    # Arrange
    agent1_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")
    agent2_id = uuid4()
    
    state = {
        "input": "Legal and financial question",
        "chat_id": uuid4(),
        "available_agents": [agent1_id, agent2_id],
        "selected_agents": SupervisorOutput({
            agent1_id: True,
            agent2_id: True
        })
    }
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock) as mock_handle:
        # Act
        result = await orchestrator.orchestrate(state, mock_worker_state)
        
        # Assert
        # Should call __handle_agent_interaction for both agents
        assert mock_handle.call_count == 2
        
        # Check that both agent IDs were processed (as strings)
        called_agent_ids = [call[1]["agent_id"] for call in mock_handle.call_args_list]
        assert str(agent1_id) in called_agent_ids
        assert str(agent2_id) in called_agent_ids


# Unit Tests for State Return

@pytest.mark.asyncio
async def test_orchestrate_returns_original_state(orchestrator, mock_worker_state, sample_state):
    """Test that orchestrate returns the original state unchanged"""
    # Arrange
    original_state = sample_state.copy()
    
    with patch.object(orchestrator, '_Orchestrator__handle_agent_interaction', new_callable=AsyncMock):
        # Act
        result = await orchestrator.orchestrate(sample_state, mock_worker_state)
        
        # Assert
        assert result == original_state
        assert result["input"] == original_state["input"]
        assert result["chat_id"] == original_state["chat_id"]
        assert result["available_agents"] == original_state["available_agents"]
        assert result["selected_agents"] == original_state["selected_agents"]


# Unit Tests for __handle_agent_interaction Method

@pytest.mark.asyncio
async def test_handle_agent_interaction_makes_http_request_to_agent():
    """Test that __handle_agent_interaction makes HTTP request to agent endpoint"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    state = {"input": "Test", "chat_id": uuid4()}
    worker_state = WorkerState(
        input="Test",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    
    mock_response = Mock()
    mock_response.json.return_value = {"final_response": "Test response"}
    
    with patch('httpx.AsyncClient') as mock_http_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.example.com',
            'HMAC_SECRET': 'test-secret',
            'MAIN_SERVER_ENDPOINT': 'test-endpoint'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers') as mock_hmac:  # Fixed path
            
            mock_hmac.return_value = {"Authorization": "Bearer test"}
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert
            # Should have made 2 HTTP calls
            assert mock_client_instance.post.call_count == 2
            
            # Check first call (agent interaction)
            first_call = mock_client_instance.post.call_args_list[0]
            expected_url = f"{agent_id}.example.com/interactions/internal/interact"
            assert first_call[0][0] == expected_url
            
            # Check that headers were used in first call
            assert "headers" in first_call[1]
            
            # Check payload contains worker_state data
            assert "json" in first_call[1]
            payload = first_call[1]["json"]
            assert payload["input"] == worker_state.input


@pytest.mark.asyncio
async def test_handle_agent_interaction_uses_worker_state_payload():
    """Test that __handle_agent_interaction uses worker_state.model_dump() as payload"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    state = {"input": "Test", "chat_id": uuid4()}
    worker_state = WorkerState(
        input="Test question",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[{"role": "human", "content": "Hello"}],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    
    mock_response = Mock()
    mock_response.json.return_value = {"final_response": "Test response"}
    
    with patch('httpx.AsyncClient') as mock_http_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.example.com',
            'HMAC_SECRET': 'test-secret',
            'MAIN_SERVER_ENDPOINT': 'test-endpoint'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers'):  # Fixed path
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert
            first_call = mock_client_instance.post.call_args_list[0]
            payload = first_call[1]["json"]
            
            # Check all worker_state fields are present
            assert payload["input"] == worker_state.input
            assert str(payload["chat_id"]) == str(worker_state.chat_id)
            assert str(payload["company_id"]) == str(worker_state.company_id)
            assert str(payload["user_id"]) == str(worker_state.user_id)
            assert payload["chat_history"] == worker_state.chat_history


@pytest.mark.asyncio
async def test_handle_agent_interaction_sends_response_to_frontend():
    """Test that __handle_agent_interaction sends agent response to frontend"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    state = {"input": "Test", "chat_id": uuid4()}
    worker_state = WorkerState(
        input="Test",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    expected_response = {"final_response": "Legal advice"}
    
    # Create a proper mock response
    mock_response = Mock()
    mock_response.json.return_value = expected_response
    
    with patch('httpx.AsyncClient') as mock_http_client:
        # Setup the async context manager properly
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.example.com',
            'HMAC_SECRET': 'test-secret',
            'MAIN_SERVER_ENDPOINT': 'test-endpoint'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers') as mock_hmac:  # Fixed path
            
            mock_hmac.return_value = {"Authorization": "Bearer test"}
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert
            websocket.send_json.assert_called_with({
                "agent_id": agent_id,
                "response": expected_response
            })


@pytest.mark.asyncio
async def test_handle_agent_interaction_saves_conversation():
    """Test that __handle_agent_interaction saves conversation to main server"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    chat_id = uuid4()
    state = {"input": "Can I fire someone?", "chat_id": chat_id}
    worker_state = WorkerState(
        input="Test",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    agent_response = {"final_response": "Legal advice"}
    
    # Create proper mock response
    mock_response = Mock()
    mock_response.json.return_value = agent_response
    
    with patch('httpx.AsyncClient') as mock_http_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.example.com',
            'HMAC_SECRET': 'test-secret',
            'MAIN_SERVER_ENDPOINT': 'test-endpoint'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers') as mock_hmac:  # Fixed path
            
            mock_hmac.return_value = {"Authorization": "Bearer test"}
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert
            # Check that both HTTP calls were made
            assert mock_client_instance.post.call_count == 2
            
            # Check the second call (save conversation)
            second_call = mock_client_instance.post.call_args_list[1]
            
            # Check URL
            expected_url = f"https://test-endpoint/interactions/internal/outgoing/{chat_id}"
            assert second_call[0][0] == expected_url
            
            # Check payload
            save_payload = second_call[1]["json"]
            assert save_payload["human_message"] == state["input"]
            assert save_payload["agent_id"] == agent_id
            assert save_payload["ai_message"] == agent_response


@pytest.mark.asyncio
async def test_handle_agent_interaction_uses_hmac_headers():
    """Test that __handle_agent_interaction uses HMAC headers for main server requests"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    state = {"input": "Test", "chat_id": uuid4()}
    worker_state = WorkerState(
        input="Test",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    
    mock_response = Mock()
    mock_response.json.return_value = {"final_response": "Test"}
    
    with patch('httpx.AsyncClient') as mock_http_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.example.com',
            'HMAC_SECRET': 'my-secret-key',
            'MAIN_SERVER_ENDPOINT': 'test-endpoint'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers') as mock_hmac:  # Fixed path
            
            expected_headers = {"Authorization": "Bearer test-token"}
            mock_hmac.return_value = expected_headers
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert - Now called TWICE (worker headers + main server headers)
            assert mock_hmac.call_count == 2
            mock_hmac.assert_has_calls([
                call("my-secret-key"),
                call("my-secret-key")
            ])
            
            # Check that headers were used in both calls
            assert mock_client_instance.post.call_count == 2
            first_call = mock_client_instance.post.call_args_list[0]
            second_call = mock_client_instance.post.call_args_list[1]
            
            assert "headers" in first_call[1]
            assert first_call[1]["headers"] == expected_headers
            assert "headers" in second_call[1]
            assert second_call[1]["headers"] == expected_headers


@pytest.mark.asyncio
async def test_handle_agent_interaction_uses_environment_variables():
    """Test that __handle_agent_interaction uses required environment variables"""
    # Arrange
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
    state = {"input": "Test", "chat_id": uuid4()}
    worker_state = WorkerState(
        input="Test",
        agents=[UUID(agent_id)],
        chat_id=uuid4(),
        company_id=uuid4(),
        chat_history=[],
        user_id=uuid4()
    )
    websocket = Mock()
    websocket.send_json = AsyncMock()
    
    mock_response = Mock()
    mock_response.json.return_value = {"final_response": "Test"}
    
    with patch('httpx.AsyncClient') as mock_http_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_http_client.return_value.__aenter__.return_value = mock_client_instance
        
        with patch.dict('os.environ', {
            'WORKER_HOST': '.test-worker.com',
            'HMAC_SECRET': 'my-secret-key',
            'MAIN_SERVER_ENDPOINT': 'my-main-server.com'
        }), \
        patch('src.workflow.orchestrator.orchestrator.generate_hmac_headers') as mock_hmac:  # Fixed path
            
            mock_hmac.return_value = {"Authorization": "Bearer test"}
            
            # Act
            await Orchestrator._Orchestrator__handle_agent_interaction(
                agent_id=agent_id,
                state=state,
                worker_state=worker_state,
                websocket=websocket
            )
            
            # Assert
            assert mock_client_instance.post.call_count == 2
            
            # Check WORKER_HOST usage (first call - agent interaction)
            first_call = mock_client_instance.post.call_args_list[0]
            agent_url = first_call[0][0]
            assert ".test-worker.com" in agent_url
            assert agent_id in agent_url
            
            # Check HMAC_SECRET usage - now called TWICE
            assert mock_hmac.call_count == 2
            mock_hmac.assert_has_calls([
                call("my-secret-key"),
                call("my-secret-key")
            ])
            
            # Check MAIN_SERVER_ENDPOINT usage (second call - main server)
            second_call = mock_client_instance.post.call_args_list[1]
            save_url = second_call[0][0]
            assert "my-main-server.com" in save_url
            assert "https://" in save_url

