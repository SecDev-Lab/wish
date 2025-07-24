"""
Context builder for AI prompt construction.

This module provides the ContextBuilder class that creates rich context
information for LLM prompts based on engagement state and conversation history.
"""

import logging
from datetime import datetime
from typing import Any

from wish_knowledge import Retriever
from wish_models import EngagementState

from .templates import PromptTemplates

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builder for creating rich context for LLM prompts.

    This class integrates engagement state, conversation history, and
    knowledge base information to create comprehensive context for AI interactions.
    """

    def __init__(
        self, retriever: Retriever | None = None, max_tokens: int = 8000, templates: PromptTemplates | None = None
    ):
        """Initialize the context builder.

        Args:
            retriever: Knowledge base retriever for RAG functionality
            max_tokens: Maximum tokens for context (default: 8000)
            templates: Prompt templates (uses default if None)
        """
        self.retriever = retriever
        self.max_tokens = max_tokens
        self.templates = templates or PromptTemplates()

        # Token allocation for different context sections
        self.token_allocation = {
            "system_prompt": 1000,
            "knowledge_context": 1500,
            "state_summary": 1500,
            "conversation_history": 2000,
            "user_input": 500,
            "response_buffer": 1500,
        }

        logger.info("Initialized ContextBuilder")

    async def build_context(
        self,
        user_input: str,
        engagement_state: EngagementState,
        conversation_history: list[dict[str, Any]] | None = None,
        mode_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build comprehensive context for LLM prompts.

        Args:
            user_input: User's natural language input
            engagement_state: Current penetration testing state
            conversation_history: Previous conversation messages
            mode_context: Additional mode-specific context

        Returns:
            Dictionary containing all context information
        """
        try:
            logger.debug(f"Building context for user input: {user_input[:50]}...")

            context: dict[str, Any] = {
                "user_input": user_input,
                "mode": engagement_state.get_current_mode(),
                "timestamp": datetime.now().isoformat(),
            }

            # Add mode-specific context
            if mode_context:
                context.update(mode_context)

            # Build knowledge context from RAG if available
            if self.retriever:
                knowledge_context = await self._build_knowledge_context(user_input, engagement_state)
                context["knowledge"] = knowledge_context

                # Build tools context
                tools_context = {"tools": [], "message": "Tool suggestions disabled"}
                context["tools"] = tools_context

            # Build state summary
            state_summary = self._build_state_summary(engagement_state)
            context["state"] = state_summary

            # Build conversation context
            if conversation_history:
                conv_context = self._build_conversation_context(conversation_history)
                context["conversation"] = conv_context

            logger.debug("Context building completed successfully")
            return context

        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            # Return minimal context on failure
            return {
                "user_input": user_input,
                "mode": engagement_state.get_current_mode(),
                "error": f"Context building failed: {str(e)}",
            }

    async def _build_knowledge_context(self, user_input: str, engagement_state: EngagementState) -> dict[str, Any]:
        """Build knowledge context using RAG retrieval.

        Args:
            user_input: User's input for query generation
            engagement_state: Current state for context

        Returns:
            Knowledge context dictionary
        """
        try:
            # Generate search query based on user input and current state
            query = self._generate_rag_query(user_input, engagement_state)

            # Retrieve relevant knowledge
            if self.retriever is not None:
                results = await self.retriever.search(query=query, limit=5)
            else:
                results = []

            if not results:
                return {"articles": [], "query": query}

            # Format results for context
            articles = []
            for result in results:
                articles.append(
                    {
                        "title": result.get("title", "Unknown"),
                        "content": result.get("content", "")[:500],  # Limit content
                        "score": result.get("score", 0.0),
                        "source": result.get("source", "HackTricks"),
                    }
                )

            return {"articles": articles, "query": query, "total_results": len(results)}

        except Exception as e:
            logger.warning(f"Failed to build knowledge context: {e}")
            return {"articles": [], "error": str(e)}

    def _generate_rag_query(self, user_input: str, engagement_state: EngagementState) -> str:
        """Generate optimized query for RAG retrieval.

        Args:
            user_input: User's natural language input
            engagement_state: Current engagement state

        Returns:
            Optimized search query
        """
        query_parts = [user_input]

        # Add mode-specific keywords
        mode_keywords = {
            "recon": ["reconnaissance", "discovery", "enumeration"],
            "enum": ["enumeration", "scanning", "service detection"],
            "exploit": ["exploitation", "vulnerability", "payload"],
        }

        current_mode = engagement_state.get_current_mode()
        if current_mode in mode_keywords:
            query_parts.extend(mode_keywords[current_mode])

        # Add service-specific keywords from discovered hosts
        active_hosts = engagement_state.get_active_hosts()
        for host in active_hosts[:3]:  # Limit to 3 hosts
            for service in host.services:
                if service.state == "open" and service.service_name:
                    query_parts.append(service.service_name)
                    if service.port in [80, 443, 8080, 8443]:
                        query_parts.append("web application")
                    elif service.port in [22]:
                        query_parts.append("ssh")
                    elif service.port in [139, 445]:
                        query_parts.append("smb")

        return " ".join(query_parts[:10])  # Limit query length

    def _build_state_summary(self, engagement_state: EngagementState) -> dict[str, Any]:
        """Build summary of current engagement state.

        Args:
            engagement_state: Current engagement state

        Returns:
            State summary dictionary
        """
        active_hosts = engagement_state.get_active_hosts()
        open_services = engagement_state.get_open_services()
        findings = list(engagement_state.findings.values())
        targets = list(engagement_state.targets.values())

        # Count findings by severity
        severity_counts: dict[str, int] = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

        # Get common services
        service_counts: dict[str, int] = {}
        for service in open_services:
            if service.service_name:
                key = f"{service.service_name}:{service.port}"
                service_counts[key] = service_counts.get(key, 0) + 1

        return {
            "mode": engagement_state.get_current_mode(),
            "targets_count": len(targets),
            "in_scope_targets": len([t for t in targets if t.in_scope]),
            "active_hosts_count": len(active_hosts),
            "open_services_count": len(open_services),
            "findings_count": len(findings),
            "severity_counts": severity_counts,
            "common_services": dict(sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "phase": self._determine_phase(engagement_state),
        }

    def _determine_phase(self, engagement_state: EngagementState) -> str:
        """Determine the current penetration testing phase.

        Args:
            engagement_state: Current engagement state

        Returns:
            Current phase string
        """
        active_hosts = engagement_state.get_active_hosts()
        findings = list(engagement_state.findings.values())
        high_severity_findings = [f for f in findings if f.severity in ["high", "critical"]]

        if not active_hosts:
            return "initial_reconnaissance"
        elif not findings:
            return "enumeration"
        elif not high_severity_findings:
            return "vulnerability_assessment"
        else:
            return "exploitation"

    def _build_conversation_context(self, conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Build context from conversation history.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Conversation context dictionary
        """
        if not conversation_history:
            return {"messages": [], "summary": "No previous conversation"}

        # Prioritize recent and important messages
        prioritized_history = self._prioritize_conversation_history(conversation_history)

        # Create summary of older messages
        recent_messages = prioritized_history[:5]
        older_messages = prioritized_history[5:]

        summary_parts = []
        if older_messages:
            actions = self._extract_actions_from_history(older_messages)
            if actions:
                summary_parts.append("Previous actions: " + ", ".join(actions))

        return {
            "messages": recent_messages,
            "summary": "; ".join(summary_parts) if summary_parts else "Limited conversation history",
            "total_messages": len(conversation_history),
        }

    def _prioritize_conversation_history(self, conversation_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prioritize conversation history by importance and recency.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Prioritized list of messages
        """

        def calculate_importance(message: dict[str, Any]) -> float:
            """Calculate importance score for a message."""
            score = 1.0
            content = message.get("content", "").lower()

            # Recent messages are more important
            timestamp = message.get("timestamp")
            if timestamp:
                try:
                    msg_time = datetime.fromisoformat(timestamp)
                    age_minutes = (datetime.now() - msg_time).total_seconds() / 60
                    recency_score = max(0.1, 1.0 - (age_minutes / 120))  # 2 hours decay
                    score *= recency_score
                except ValueError:
                    pass

            # Commands and discoveries are more important
            if any(keyword in content for keyword in ["execute", "run", "scan", "found", "discovered"]):
                score *= 1.5

            # Errors and warnings are important
            if any(keyword in content for keyword in ["error", "failed", "warning"]):
                score *= 1.3

            return score

        # Sort by importance score
        return sorted(conversation_history, key=calculate_importance, reverse=True)

    def _extract_actions_from_history(self, messages: list[dict[str, Any]]) -> list[str]:
        """Extract key actions from conversation history.

        Args:
            messages: List of conversation messages

        Returns:
            List of action descriptions
        """
        actions = []

        for message in messages:
            content = message.get("content", "").lower()

            # Look for specific action patterns
            if "nmap" in content or "scan" in content:
                actions.append("network scanning")
            elif "gobuster" in content or "dirb" in content:
                actions.append("directory enumeration")
            elif "nikto" in content:
                actions.append("web vulnerability scanning")
            elif "hydra" in content or "medusa" in content:
                actions.append("credential attacks")
            elif "metasploit" in content or "exploit" in content:
                actions.append("exploitation attempts")

        # Remove duplicates while preserving order
        return list(dict.fromkeys(actions))
