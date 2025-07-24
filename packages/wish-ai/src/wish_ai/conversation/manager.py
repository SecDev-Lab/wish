"""
Conversation manager for maintaining AI interaction history.

This module provides the ConversationManager class for tracking and
managing conversation history across AI interactions in wish.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class ConversationManager:
    """Manager for AI conversation history and context.

    This class handles storage, retrieval, and summarization of conversation
    history to maintain context across multiple AI interactions.
    """

    def __init__(self, max_messages: int = 100, max_age_hours: int = 24, summary_threshold: int = 50):
        """Initialize the conversation manager.

        Args:
            max_messages: Maximum number of messages to keep (default: 100)
            max_age_hours: Maximum age of messages in hours (default: 24)
            summary_threshold: Number of messages before summarization (default: 50)
        """
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.summary_threshold = summary_threshold

        self._messages: list[ConversationMessage] = []
        self._session_id: str | None = None

        logger.info(f"Initialized ConversationManager (max_messages={max_messages})")

    def start_session(self, session_id: str) -> None:
        """Start a new conversation session.

        Args:
            session_id: Unique identifier for the session
        """
        self._session_id = session_id
        self._messages.clear()
        logger.info(f"Started new conversation session: {session_id}")

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new message to the conversation history.

        Args:
            role: Message role ("user", "assistant", "system")
            content: Message content
            metadata: Additional metadata for the message
        """
        if role not in ["user", "assistant", "system"]:
            raise ValueError(f"Invalid role: {role}")

        message = ConversationMessage(role=role, content=content, timestamp=datetime.now(), metadata=metadata or {})

        self._messages.append(message)
        logger.debug(f"Added {role} message ({len(content)} chars)")

        # Clean up old messages if needed
        self._cleanup_messages()

    def add_user_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a user message to the conversation.

        Args:
            content: User message content
            metadata: Additional metadata
        """
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add an assistant message to the conversation.

        Args:
            content: Assistant message content
            metadata: Additional metadata
        """
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a system message to the conversation.

        Args:
            content: System message content
            metadata: Additional metadata
        """
        self.add_message("system", content, metadata)

    def get_recent_messages(self, limit: int = 10) -> list[ConversationMessage]:
        """Get the most recent messages.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of recent messages, newest first
        """
        return list(reversed(self._messages[-limit:]))

    def get_messages_by_role(self, role: str) -> list[ConversationMessage]:
        """Get all messages from a specific role.

        Args:
            role: Message role to filter by

        Returns:
            List of messages from the specified role
        """
        return [msg for msg in self._messages if msg.role == role]

    def get_context_for_ai(self, max_messages: int = 20) -> list[dict[str, str]]:
        """Get conversation context formatted for AI consumption.

        Args:
            max_messages: Maximum number of messages to include

        Returns:
            List of messages formatted for AI (role, content)
        """
        recent_messages = self._messages[-max_messages:]

        # Convert to AI format (role, content)
        ai_context = []
        for msg in recent_messages:
            ai_context.append({"role": msg.role, "content": msg.content})

        return ai_context

    def search_messages(self, query: str, role: str | None = None, limit: int = 10) -> list[ConversationMessage]:
        """Search for messages containing specific text.

        Args:
            query: Text to search for
            role: Optional role filter
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        query_lower = query.lower()
        results = []

        for msg in reversed(self._messages):  # Search newest first
            if role and msg.role != role:
                continue

            if query_lower in msg.content.lower():
                results.append(msg)

                if len(results) >= limit:
                    break

        return results

    def get_conversation_summary(self) -> dict[str, Any]:
        """Get a summary of the current conversation.

        Returns:
            Dictionary containing conversation statistics and summary
        """
        if not self._messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "system_messages": 0,
                "duration_minutes": 0,
                "topics": [],
                "last_activity": None,
            }

        # Count messages by role
        role_counts: dict[str, int] = {}
        for msg in self._messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

        # Calculate duration
        first_message = self._messages[0]
        last_message = self._messages[-1]
        duration = (last_message.timestamp - first_message.timestamp).total_seconds() / 60

        # Extract topics (simple keyword extraction)
        topics = self._extract_conversation_topics()

        return {
            "total_messages": len(self._messages),
            "user_messages": role_counts.get("user", 0),
            "assistant_messages": role_counts.get("assistant", 0),
            "system_messages": role_counts.get("system", 0),
            "duration_minutes": round(duration, 1),
            "topics": topics,
            "last_activity": last_message.timestamp.isoformat(),
            "session_id": self._session_id,
        }

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self._messages.clear()
        logger.info("Cleared conversation history")

    def export_conversation(self) -> list[dict[str, Any]]:
        """Export the full conversation for serialization.

        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self._messages]

    def import_conversation(self, messages: list[dict[str, Any]]) -> None:
        """Import conversation from serialized data.

        Args:
            messages: List of message dictionaries
        """
        self._messages.clear()

        for msg_data in messages:
            try:
                message = ConversationMessage.from_dict(msg_data)
                self._messages.append(message)
            except Exception as e:
                logger.warning(f"Failed to import message: {e}")

        logger.info(f"Imported {len(self._messages)} messages")

    def _cleanup_messages(self) -> None:
        """Clean up old messages based on age and count limits."""
        # Remove messages older than max_age_hours
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        self._messages = [msg for msg in self._messages if msg.timestamp > cutoff_time]

        # Keep only the most recent max_messages
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]
            logger.debug(f"Trimmed conversation to {self.max_messages} messages")

    def _extract_conversation_topics(self) -> list[str]:
        """Extract key topics from the conversation.

        Returns:
            List of identified topics/keywords
        """
        # Simple topic extraction based on common pentesting terms
        topic_keywords = {
            "scanning": ["nmap", "scan", "masscan", "port"],
            "enumeration": ["gobuster", "dirb", "enum", "enumerate"],
            "web_testing": ["burp", "nikto", "web", "http", "https"],
            "exploitation": ["exploit", "metasploit", "payload", "shell"],
            "credentials": ["hydra", "medusa", "password", "credential"],
            "post_exploitation": ["privilege", "escalation", "lateral", "persistence"],
        }

        # Count occurrences of topic keywords
        topic_counts: dict[str, int] = {}
        for msg in self._messages:
            content_lower = msg.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Return topics sorted by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics if count >= 2]  # Minimum 2 mentions
