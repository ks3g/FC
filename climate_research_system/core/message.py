"""
Message system for inter-agent communication.
"""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class MessageType(Enum):
    """Types of messages agents can send/receive."""
    REQUEST = "request"           # Request for data/action
    RESPONSE = "response"         # Response to a request
    ERROR = "error"               # Error notification
    STATUS = "status"             # Status update
    VALIDATION = "validation"     # Validation request/result
    NOTIFICATION = "notification" # General notification


class Message:
    """
    Message object for agent communication.

    Attributes:
        id: Unique message identifier
        type: Type of message
        sender: Agent ID that sent the message
        recipient: Agent ID that should receive the message (None for broadcast)
        payload: Message data
        timestamp: When message was created
        correlation_id: ID to correlate request/response pairs
    """

    def __init__(
        self,
        type: MessageType,
        sender: str,
        payload: Any = None,
        recipient: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.type = type
        self.sender = sender
        self.recipient = recipient
        self.payload = payload
        self.timestamp = datetime.now()
        self.correlation_id = correlation_id or self.id

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        msg = cls(
            type=MessageType(data['type']),
            sender=data['sender'],
            payload=data.get('payload'),
            recipient=data.get('recipient'),
            correlation_id=data.get('correlation_id')
        )
        msg.id = data['id']
        msg.timestamp = datetime.fromisoformat(data['timestamp'])
        return msg

    def create_response(self, sender: str, payload: Any) -> 'Message':
        """Create a response message to this message."""
        return Message(
            type=MessageType.RESPONSE,
            sender=sender,
            recipient=self.sender,
            payload=payload,
            correlation_id=self.correlation_id
        )

    def create_error(self, sender: str, error: str) -> 'Message':
        """Create an error message in response to this message."""
        return Message(
            type=MessageType.ERROR,
            sender=sender,
            recipient=self.sender,
            payload={'error': error, 'original_message_id': self.id},
            correlation_id=self.correlation_id
        )

    def __repr__(self) -> str:
        return f"Message(type={self.type.value}, sender={self.sender}, recipient={self.recipient})"
