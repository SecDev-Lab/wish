"""
Tests for conversation management module.
"""

from datetime import datetime, timedelta

import pytest

from wish_ai.conversation import ConversationManager
from wish_ai.conversation.manager import ConversationMessage


class TestConversationMessage:
    """Tests for ConversationMessage dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        timestamp = datetime.now()
        message = ConversationMessage(
            role="user", content="Test message", timestamp=timestamp, metadata={"source": "test"}
        )

        assert message.role == "user"
        assert message.content == "Test message"
        assert message.timestamp == timestamp
        assert message.metadata["source"] == "test"

    def test_to_dict(self):
        """Test message to dictionary conversion."""
        timestamp = datetime.now()
        message = ConversationMessage(
            role="assistant", content="Response message", timestamp=timestamp, metadata={"model": "gpt-4"}
        )

        result = message.to_dict()

        assert result["role"] == "assistant"
        assert result["content"] == "Response message"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["metadata"]["model"] == "gpt-4"

    def test_from_dict(self):
        """Test message creation from dictionary."""
        timestamp = datetime.now()
        data = {
            "role": "system",
            "content": "System message",
            "timestamp": timestamp.isoformat(),
            "metadata": {"type": "notification"},
        }

        message = ConversationMessage.from_dict(data)

        assert message.role == "system"
        assert message.content == "System message"
        assert message.timestamp == timestamp
        assert message.metadata["type"] == "notification"


class TestConversationManager:
    """Tests for ConversationManager class."""

    def test_init(self):
        """Test ConversationManager initialization."""
        manager = ConversationManager(max_messages=50, max_age_hours=12)

        assert manager.max_messages == 50
        assert manager.max_age_hours == 12
        assert len(manager._messages) == 0
        assert manager._session_id is None

    def test_start_session(self):
        """Test starting a new session."""
        manager = ConversationManager()

        # Add some messages first
        manager.add_message("user", "test message")
        assert len(manager._messages) == 1

        # Start new session should clear messages
        manager.start_session("test-session-123")

        assert manager._session_id == "test-session-123"
        assert len(manager._messages) == 0

    def test_add_message(self):
        """Test adding messages to conversation."""
        manager = ConversationManager()

        manager.add_message("user", "Hello", {"source": "test"})

        assert len(manager._messages) == 1
        message = manager._messages[0]
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.metadata["source"] == "test"

    def test_add_message_invalid_role(self):
        """Test adding message with invalid role."""
        manager = ConversationManager()

        with pytest.raises(ValueError, match="Invalid role"):
            manager.add_message("invalid_role", "test message")

    def test_add_specific_role_messages(self):
        """Test convenience methods for specific roles."""
        manager = ConversationManager()

        manager.add_user_message("User input", {"action": "query"})
        manager.add_assistant_message("AI response", {"model": "gpt-4"})
        manager.add_system_message("System notification", {"type": "info"})

        assert len(manager._messages) == 3
        assert manager._messages[0].role == "user"
        assert manager._messages[1].role == "assistant"
        assert manager._messages[2].role == "system"

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        manager = ConversationManager()

        # Add multiple messages
        for i in range(15):
            manager.add_message("user", f"Message {i}")

        # Get recent messages (should be newest first)
        recent = manager.get_recent_messages(limit=5)

        assert len(recent) == 5
        assert recent[0].content == "Message 14"  # Newest first
        assert recent[4].content == "Message 10"

    def test_get_messages_by_role(self):
        """Test filtering messages by role."""
        manager = ConversationManager()

        manager.add_user_message("User 1")
        manager.add_assistant_message("Assistant 1")
        manager.add_user_message("User 2")
        manager.add_system_message("System 1")

        user_messages = manager.get_messages_by_role("user")
        assistant_messages = manager.get_messages_by_role("assistant")

        assert len(user_messages) == 2
        assert len(assistant_messages) == 1
        assert user_messages[0].content == "User 1"
        assert assistant_messages[0].content == "Assistant 1"

    def test_get_context_for_ai(self):
        """Test getting context formatted for AI."""
        manager = ConversationManager()

        manager.add_user_message("What is nmap?")
        manager.add_assistant_message("Nmap is a network scanner")
        manager.add_user_message("How do I use it?")

        context = manager.get_context_for_ai(max_messages=2)

        assert len(context) == 2
        assert context[0]["role"] == "assistant"
        assert context[0]["content"] == "Nmap is a network scanner"
        assert context[1]["role"] == "user"
        assert context[1]["content"] == "How do I use it?"

    def test_search_messages(self):
        """Test searching messages by content."""
        manager = ConversationManager()

        manager.add_user_message("Run nmap scan")
        manager.add_assistant_message("Running nmap -sV target")
        manager.add_user_message("Start gobuster enumeration")
        manager.add_assistant_message("Starting directory enumeration")

        # Search for nmap
        nmap_results = manager.search_messages("nmap")
        assert len(nmap_results) == 2

        # Search for enumeration
        enum_results = manager.search_messages("enumeration")
        assert len(enum_results) == 2

        # Search with role filter
        user_nmap = manager.search_messages("nmap", role="user")
        assert len(user_nmap) == 1
        assert user_nmap[0].content == "Run nmap scan"

    def test_get_conversation_summary(self):
        """Test conversation summary generation."""
        manager = ConversationManager()
        manager.start_session("test-session")

        # Add various messages
        manager.add_user_message("Run nmap scan")
        manager.add_assistant_message("Running network scan")
        manager.add_user_message("Start enumeration")
        manager.add_system_message("Scan completed")

        summary = manager.get_conversation_summary()

        assert summary["total_messages"] == 4
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 1
        assert summary["system_messages"] == 1
        assert summary["session_id"] == "test-session"
        assert "last_activity" in summary
        assert isinstance(summary["duration_minutes"], float)

    def test_conversation_summary_empty(self):
        """Test summary with no messages."""
        manager = ConversationManager()

        summary = manager.get_conversation_summary()

        assert summary["total_messages"] == 0
        assert summary["duration_minutes"] == 0
        assert summary["topics"] == []
        assert summary["last_activity"] is None

    def test_clear_history(self):
        """Test clearing conversation history."""
        manager = ConversationManager()

        manager.add_user_message("Test message")
        assert len(manager._messages) == 1

        manager.clear_history()
        assert len(manager._messages) == 0

    def test_export_import_conversation(self):
        """Test conversation export and import."""
        manager = ConversationManager()

        # Add messages
        manager.add_user_message("Hello")
        manager.add_assistant_message("Hi there")
        manager.add_system_message("Session started")

        # Export
        exported = manager.export_conversation()
        assert len(exported) == 3
        assert all("role" in msg and "content" in msg for msg in exported)

        # Clear and import
        manager.clear_history()
        assert len(manager._messages) == 0

        manager.import_conversation(exported)
        assert len(manager._messages) == 3
        assert manager._messages[0].content == "Hello"
        assert manager._messages[1].content == "Hi there"
        assert manager._messages[2].content == "Session started"

    def test_message_cleanup_by_count(self):
        """Test message cleanup based on count limit."""
        manager = ConversationManager(max_messages=5)

        # Add more messages than the limit
        for i in range(10):
            manager.add_message("user", f"Message {i}")

        # Should only keep the last 5 messages
        assert len(manager._messages) == 5
        assert manager._messages[0].content == "Message 5"
        assert manager._messages[4].content == "Message 9"

    def test_message_cleanup_by_age(self):
        """Test message cleanup based on age limit."""
        manager = ConversationManager(max_age_hours=1)

        # Mock old timestamp
        old_time = datetime.now() - timedelta(hours=2)
        old_message = ConversationMessage(role="user", content="Old message", timestamp=old_time, metadata={})
        manager._messages.append(old_message)

        # Add new message (this triggers cleanup)
        manager.add_message("user", "New message")

        # Old message should be removed
        assert len(manager._messages) == 1
        assert manager._messages[0].content == "New message"

    def test_extract_conversation_topics(self):
        """Test topic extraction from conversation."""
        manager = ConversationManager()

        # Add messages with various pentesting topics
        manager.add_user_message("Run nmap scan on the target")
        manager.add_assistant_message("Starting nmap port scan")
        manager.add_user_message("Use gobuster for directory enumeration")
        manager.add_assistant_message("Running web enumeration with gobuster")
        manager.add_user_message("Try hydra for password attacks")
        manager.add_assistant_message("Using hydra for credential attacks")

        summary = manager.get_conversation_summary()
        topics = summary["topics"]

        # Should identify scanning, enumeration, and credentials topics
        assert "scanning" in topics
        assert "enumeration" in topics
        assert "credentials" in topics

        # Topics should be sorted by frequency
        assert topics.index("scanning") < len(topics)  # Should be present
