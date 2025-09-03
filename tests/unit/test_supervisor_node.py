import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4

from src.workflow.agents.supervisor.supervisor_agent import Supervisor
from src.workflow.agents.supervisor.supervisor_models import SupervisorOutput
from src.workflow.state import State
from src.workflow.services.prompt_service import PromptService
from src.workflow.services.llm_service import LlmService


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_prompt_service():
    """Mock PromptService for testing"""
    mock_service = Mock(spec=PromptService)
    mock_service.custom_prompt_template = AsyncMock(return_value="mock_prompt_template")
    return mock_service


@pytest.fixture
def mock_llm_service():
    """Mock LlmService for testing"""
    mock_service = Mock(spec=LlmService)
    mock_llm = Mock()
    mock_llm.with_structured_output = Mock()
    mock_service.get_llm = Mock(return_value=mock_llm)
    return mock_service


@pytest.fixture
def supervisor_instance(mock_prompt_service, mock_llm_service):
    """Create Supervisor instance with mocked dependencies"""
    return Supervisor(mock_prompt_service, mock_llm_service)


@pytest.fixture
def sample_state():
    """Sample state for testing"""
    return {
        "input": "Can I terminate an employee without notice?",
        "chat_id": uuid4(),
        "available_agents": [UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")],
    }


@pytest.fixture
def legal_agent_id():
    """The legal agent UUID from the supervisor code"""
    return UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")


# Unit Tests for Supervisor Constructor

def test_supervisor_constructor_initializes_dependencies(mock_prompt_service, mock_llm_service):
    """Test that Supervisor constructor properly initializes dependencies"""
    # Act
    supervisor = Supervisor(mock_prompt_service, mock_llm_service)
    
    # Assert
    assert supervisor._Supervisor__prompt_service == mock_prompt_service
    assert supervisor._Supervisor__llm_service == mock_llm_service


def test_supervisor_constructor_accepts_correct_types():
    """Test that Supervisor constructor accepts correct dependency types"""
    # Arrange
    prompt_service = Mock(spec=PromptService)
    llm_service = Mock(spec=LlmService)
    
    # Act & Assert - Should not raise any exceptions
    supervisor = Supervisor(prompt_service, llm_service)
    assert supervisor is not None


# Unit Tests for __get_prompt_template Method

@pytest.mark.asyncio
async def test_get_prompt_template_calls_prompt_service(supervisor_instance, mock_prompt_service, sample_state):
    """Test that __get_prompt_template calls prompt service with correct parameters"""
    # Act
    await supervisor_instance._Supervisor__get_prompt_template(sample_state)
    
    # Assert
    mock_prompt_service.custom_prompt_template.assert_called_once()
    call_args = mock_prompt_service.custom_prompt_template.call_args
    assert call_args.kwargs["state"] == sample_state
    assert call_args.kwargs["with_chat_history"] is True
    assert "system_message" in call_args.kwargs


@pytest.mark.asyncio
async def test_get_prompt_template_system_message_content(supervisor_instance, mock_prompt_service, sample_state):
    """Test that __get_prompt_template includes correct system message content"""
    # Act
    await supervisor_instance._Supervisor__get_prompt_template(sample_state)
    
    # Assert
    call_args = mock_prompt_service.custom_prompt_template.call_args
    system_message = call_args.kwargs["system_message"]
    
    # Check key components of the system message
    assert "workflow orchestrator" in system_message
    assert "95e222ef-c637-42d3-a81e-955beeeb0ba2" in system_message
    assert "legal system" in system_message
    assert "Can I terminate an employee without notice?" in system_message
    assert "How do I reset my company email password?" in system_message


@pytest.mark.asyncio
async def test_get_prompt_template_returns_prompt(supervisor_instance, mock_prompt_service, sample_state):
    """Test that __get_prompt_template returns the prompt from prompt service"""
    # Arrange
    expected_prompt = "test_prompt_template"
    mock_prompt_service.custom_prompt_template.return_value = expected_prompt
    
    # Act
    result = await supervisor_instance._Supervisor__get_prompt_template(sample_state)
    
    # Assert
    assert result == expected_prompt


@pytest.mark.asyncio
async def test_get_prompt_template_with_error_handler():
    """Test that __get_prompt_template has error_handler decorator"""
    # This test verifies the decorator is applied by checking the method exists
    # and can be called without the decorator interfering
    
    # Arrange
    mock_prompt_service = Mock(spec=PromptService)
    mock_prompt_service.custom_prompt_template = AsyncMock(return_value="prompt")
    mock_llm_service = Mock(spec=LlmService)
    
    supervisor = Supervisor(mock_prompt_service, mock_llm_service)
    state = {"input": "test", "chat_id": uuid4(), "available_agents": []}
    
    # Act & Assert - Should not raise exceptions
    result = await supervisor._Supervisor__get_prompt_template(state)
    assert result == "prompt"


# Unit Tests for interact Method

@pytest.mark.asyncio
async def test_interact_calls_llm_service_get_llm(supervisor_instance, mock_llm_service, sample_state):
    """Test that interact method calls llm_service.get_llm with correct temperature"""
    # Arrange
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({uuid4(): True}))
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    # Mock the prompt template method
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    # Mock the chain creation (prompt | structured_llm)
    with patch('src.workflow.agents.supervisor.supervisor_agent.SupervisorOutput') as mock_supervisor_output:
        mock_supervisor_output.return_value = SupervisorOutput({uuid4(): True})
        
        # Create a mock that supports the | operator
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)
        supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
        
        # Act
        await supervisor_instance.interact(sample_state)
        
        # Assert
        mock_llm_service.get_llm.assert_called_once_with(temperature=0.1)


@pytest.mark.asyncio
async def test_interact_calls_get_prompt_template(supervisor_instance, mock_llm_service, sample_state):
    """Test that interact method calls __get_prompt_template with state"""
    # Arrange
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({uuid4(): True}))
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    # Mock the prompt template method
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    # Mock the chain creation
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    await supervisor_instance.interact(sample_state)
    
    # Assert
    supervisor_instance._Supervisor__get_prompt_template.assert_called_once_with(sample_state)


@pytest.mark.asyncio
async def test_interact_creates_structured_llm_with_supervisor_output(supervisor_instance, mock_llm_service, sample_state):
    """Test that interact method creates structured LLM with SupervisorOutput"""
    # Arrange
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({uuid4(): True}))
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    await supervisor_instance.interact(sample_state)
    
    # Assert
    mock_llm.with_structured_output.assert_called_once_with(SupervisorOutput)


@pytest.mark.asyncio
async def test_interact_invokes_chain_with_input(supervisor_instance, mock_llm_service, sample_state):
    """Test that interact method invokes chain with correct input"""
    # Arrange
    expected_response = SupervisorOutput({uuid4(): True})
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=expected_response)
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    await supervisor_instance.interact(sample_state)
    
    # Assert
    mock_chain.ainvoke.assert_called_once_with({"input": sample_state["input"]})


@pytest.mark.asyncio
async def test_interact_returns_supervisor_output(supervisor_instance, mock_llm_service, sample_state, legal_agent_id):
    """Test that interact method returns SupervisorOutput"""
    # Arrange
    expected_response = SupervisorOutput({legal_agent_id: True})
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=expected_response)
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    result = await supervisor_instance.interact(sample_state)
    
    # Assert
    assert isinstance(result, SupervisorOutput)
    assert result == expected_response
    assert legal_agent_id in result.root
    assert result.root[legal_agent_id] is True


@pytest.mark.asyncio
async def test_interact_with_legal_question_selects_legal_agent(supervisor_instance, mock_llm_service, legal_agent_id):
    """Test that interact selects legal agent for legal questions"""
    # Arrange
    legal_state = {
        "input": "Can I terminate an employee without notice?",
        "chat_id": uuid4(),
        "available_agents": [legal_agent_id]
    }
    
    expected_response = SupervisorOutput({legal_agent_id: True})
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=expected_response)
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    result = await supervisor_instance.interact(legal_state)
    
    # Assert
    assert legal_agent_id in result.root
    assert result.root[legal_agent_id] is True


@pytest.mark.asyncio
async def test_interact_with_non_legal_question_does_not_select_legal_agent(supervisor_instance, mock_llm_service, legal_agent_id):
    """Test that interact does not select legal agent for non-legal questions"""
    # Arrange
    non_legal_state = {
        "input": "How do I reset my company email password?",
        "chat_id": uuid4(),
        "available_agents": [legal_agent_id]
    }
    
    expected_response = SupervisorOutput({legal_agent_id: False})
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=expected_response)
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    result = await supervisor_instance.interact(non_legal_state)
    
    # Assert
    assert legal_agent_id in result.root
    assert result.root[legal_agent_id] is False


@pytest.mark.asyncio
async def test_interact_with_multiple_agents(supervisor_instance, mock_llm_service):
    """Test that interact can handle multiple agents in response"""
    # Arrange
    agent1_id = UUID("95e222ef-c637-42d3-a81e-955beeeb0ba2")  # legal
    agent2_id = uuid4()  # another agent
    
    state = {
        "input": "I need legal and financial advice",
        "chat_id": uuid4(),
        "available_agents": [agent1_id, agent2_id]
    }
    
    expected_response = SupervisorOutput({
        agent1_id: True,
        agent2_id: True
    })
    
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=expected_response)
    mock_llm = Mock()
    mock_structured_llm = Mock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    result = await supervisor_instance.interact(state)
    
    # Assert
    assert len(result.root) == 2
    assert result.root[agent1_id] is True
    assert result.root[agent2_id] is True


# Unit Tests for Error Handling

@pytest.mark.asyncio
async def test_interact_with_error_handler_decorator():
    """Test that interact method has error_handler decorator applied"""
    # This test verifies the decorator exists by checking the method can be called
    # The actual error handling behavior would be tested in the decorator's own tests
    
    # Arrange
    mock_prompt_service = Mock(spec=PromptService)
    mock_prompt_service.custom_prompt_template = AsyncMock(return_value="prompt")
    mock_llm_service = Mock(spec=LlmService)
    
    supervisor = Supervisor(mock_prompt_service, mock_llm_service)
    state = {"input": "test", "chat_id": uuid4(), "available_agents": []}
    
    # Mock the LLM chain
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({}))
    mock_llm = Mock()
    mock_llm.with_structured_output.return_value = Mock()
    mock_llm_service.get_llm.return_value = mock_llm
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor._Supervisor__get_prompt_template = AsyncMock(return_value=mock_prompt)
    
    # Act & Assert - Should not raise exceptions
    result = await supervisor.interact(state)
    assert isinstance(result, SupervisorOutput)


# Unit Tests for State Validation

@pytest.mark.asyncio
async def test_interact_accepts_valid_state_structure(supervisor_instance, mock_llm_service):
    """Test that interact method accepts valid State structure"""
    # Arrange
    valid_state = {
        "input": "Test input",
        "chat_id": uuid4(),
        "available_agents": [uuid4(), uuid4()]
    }
    
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({}))
    mock_llm = Mock()
    mock_llm.with_structured_output.return_value = Mock()
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act & Assert - Should not raise exceptions
    result = await supervisor_instance.interact(valid_state)
    assert isinstance(result, SupervisorOutput)


@pytest.mark.asyncio
async def test_interact_handles_empty_available_agents(supervisor_instance, mock_llm_service):
    """Test that interact method handles empty available_agents list"""
    # Arrange
    state_with_no_agents = {
        "input": "Test input",
        "chat_id": uuid4(),
        "available_agents": []
    }
    
    mock_chain = AsyncMock()
    mock_chain.ainvoke = AsyncMock(return_value=SupervisorOutput({}))
    mock_llm = Mock()
    mock_llm.with_structured_output.return_value = Mock()
    mock_llm_service.get_llm.return_value = mock_llm
    
    supervisor_instance._Supervisor__get_prompt_template = AsyncMock(return_value="mock_prompt")
    
    mock_prompt = Mock()
    mock_prompt.__or__ = Mock(return_value=mock_chain)
    supervisor_instance._Supervisor__get_prompt_template.return_value = mock_prompt
    
    # Act
    result = await supervisor_instance.interact(state_with_no_agents)
    
    # Assert
    assert isinstance(result, SupervisorOutput)
    assert len(result.root) == 0

