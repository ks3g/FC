"""
Base Agent class for the orchestration system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .message import Message, MessageType
from .llm_client import LLMClient, MockLLMClient


class AgentStatus(Enum):
    """Agent operational status."""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"


class Agent(ABC):
    """
    Base class for all agents in the system.

    Each agent has:
    - Unique ID and name
    - Status tracking
    - Message handling capabilities
    - Data collection/validation logic
    - Result storage
    """

    def __init__(self, agent_id: str, name: str, config: Optional[Dict] = None):
        """
        Initialize agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.results = {}
        self.errors = []
        self.messages = []
        self.logger = self._setup_logger()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Initialize LLM client if configured
        self.llm = self._initialize_llm()

    def _setup_logger(self) -> logging.Logger:
        """Setup agent logger."""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _initialize_llm(self) -> Optional[LLMClient]:
        """
        Initialize LLM client based on configuration.

        Returns:
            LLMClient instance or MockLLMClient if no API key
        """
        llm_config = self.config.get('llm', {})

        if not llm_config:
            # Use mock client by default
            self.logger.info("No LLM config found, using MockLLMClient")
            return MockLLMClient()

        provider = llm_config.get('provider', 'anthropic')
        model = llm_config.get('model', 'claude-3-5-sonnet-20241022')
        api_key = llm_config.get('api_key')
        api_base = llm_config.get('api_base')
        api_type = llm_config.get('api_type')
        api_version = llm_config.get('api_version')

        try:
            client = LLMClient(
                provider=provider,
                model=model,
                api_key=api_key,
                api_base=api_base,
                api_type=api_type,
                api_version=api_version
            )
            self.logger.info(f"Initialized LLM: {provider}/{model}")
            return client
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM client: {e}. Using mock.")
            return MockLLMClient()

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's main task.

        Args:
            task: Task parameters

        Returns:
            Results dictionary
        """
        pass

    @abstractmethod
    def validate(self, data: Any) -> Dict[str, Any]:
        """
        Validate collected data.

        Args:
            data: Data to validate

        Returns:
            Validation result with 'valid' (bool) and 'errors' (list)
        """
        pass

    def handle_message(self, message: Message) -> Optional[Message]:
        """
        Handle incoming message.

        Args:
            message: Incoming message

        Returns:
            Response message if applicable
        """
        self.messages.append(message)
        self.logger.info(f"Received message: {message.type.value} from {message.sender}")

        try:
            if message.type == MessageType.REQUEST:
                return self._handle_request(message)
            elif message.type == MessageType.VALIDATION:
                return self._handle_validation(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.type}")
                return None
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            return message.create_error(self.agent_id, str(e))

    def _handle_request(self, message: Message) -> Message:
        """Handle a REQUEST message."""
        self.set_status(AgentStatus.WORKING)
        try:
            result = self.execute(message.payload)
            self.results = result
            self.set_status(AgentStatus.COMPLETED)
            return message.create_response(self.agent_id, result)
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            self.add_error(str(e))
            raise

    def _handle_validation(self, message: Message) -> Message:
        """Handle a VALIDATION message."""
        validation_result = self.validate(message.payload)
        return message.create_response(self.agent_id, validation_result)

    def set_status(self, status: AgentStatus) -> None:
        """Update agent status."""
        self.status = status
        self.updated_at = datetime.now()
        self.logger.info(f"Status changed to: {status.value}")

    def add_error(self, error: str) -> None:
        """Record an error."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        self.errors.append(error_entry)
        self.logger.error(error)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current agent state.

        Returns:
            State dictionary
        """
        llm_info = {}
        if self.llm:
            llm_info = {
                'provider': getattr(self.llm, 'provider', 'mock'),
                'model': getattr(self.llm, 'model', 'mock-model')
            }

        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'results': self.results,
            'errors': self.errors,
            'config': self.config,
            'llm': llm_info,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }

    def reset(self) -> None:
        """Reset agent to initial state."""
        self.status = AgentStatus.IDLE
        self.results = {}
        self.errors = []
        self.messages = []
        self.updated_at = datetime.now()
        self.logger.info("Agent reset")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, status={self.status.value})"
