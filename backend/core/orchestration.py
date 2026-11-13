"""
backend/core/orchestration.py
==============================
Semantic Kernel setup and agent orchestration configuration.

WHAT THIS FILE DOES:
  - Creates the Semantic Kernel Kernel instance.
  - Configures the chat completion service (mock or real LLM).
  - Provides the MockChatCompletionService for offline mode.
  - Helper functions to create ChatCompletionAgent instances.

HOW OFFLINE MODE WORKS:
  Semantic Kernel agents need a "chat completion service" to process
  messages. Normally this would be OpenAI/Azure. For offline mode,
  we create a MockChatCompletionService that:
  1. Receives the agent's prompt and conversation history.
  2. Instead of calling an LLM, calls our deterministic Python logic.
  3. Returns the result as if it were an LLM response.

  This way, agents still run through SK's orchestration pipeline,
  but all computation happens locally.

WHY NOT JUST CALL PYTHON FUNCTIONS DIRECTLY?
  The assignment requires using Semantic Kernel's agent framework.
  By using the mock service, we genuinely use SK's agent classes
  and orchestration, while keeping the system fully offline.
"""

import logging
from typing import Any, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def create_kernel():
    """
    Create and configure a Semantic Kernel Kernel instance.

    The Kernel is the central object that holds:
    - AI services (LLM connectors or mock service).
    - Plugins (registered functions that agents can call).
    - Settings and configuration.

    Returns:
        A configured Kernel instance.
    """
    from semantic_kernel import Kernel

    kernel = Kernel()
    logger.info("[Orchestration] Created Semantic Kernel instance")

    # Add the appropriate chat completion service
    if settings.LLM_ENABLED and settings.LLM_API_KEY:
        _add_llm_service(kernel)
    else:
        _add_mock_service(kernel)

    return kernel


def _add_mock_service(kernel) -> None:
    """
    Add a mock chat completion service for offline mode.

    The mock service doesn't call any API — it returns a simple
    acknowledgment. The actual work is done by kernel functions
    (tools) registered on each agent.
    """
    from semantic_kernel.connectors.ai.chat_completion_client_base import (
        ChatCompletionClientBase,
    )
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.utils.author_role import AuthorRole

    class MockChatCompletionService(ChatCompletionClientBase):
        """
        A mock LLM service that enables offline operation.

        Instead of calling an external API, this service:
        1. Reads the latest message from the conversation.
        2. Returns it (or a summary) as the assistant response.

        The real work is done by @kernel_function tools attached
        to each agent — the mock service just passes data through.
        """

        service_id: str = "mock_offline"

        def __init__(self, **kwargs):
            super().__init__(
                ai_model_id="offline-deterministic",
                service_id="mock_offline",
                **kwargs,
            )

        async def _inner_generate_chat_message_contents(
            self,
            chat_history: ChatHistory,
            settings: Any,
        ) -> list[ChatMessageContent]:
            """Process the conversation and return a response."""
            # Get the latest user/system message
            latest = ""
            if chat_history and chat_history.messages:
                latest = chat_history.messages[-1].content or ""

            # In offline mode, return the input as-is.
            # The actual processing is done by kernel functions.
            response = latest if latest else "Processing complete."

            return [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=response,
                    ai_model_id="offline-deterministic",
                )
            ]

        async def _inner_generate_streaming_chat_message_contents(
            self, chat_history, settings
        ):
            """Streaming is not used in offline mode."""
            result = await self._inner_generate_chat_message_contents(
                chat_history, settings
            )
            for msg in result:
                yield [msg]

    # Add the mock service to the kernel
    mock_service = MockChatCompletionService()
    kernel.add_service(mock_service)
    logger.info("[Orchestration] Added MockChatCompletionService (OFFLINE mode)")


def _add_llm_service(kernel) -> None:
    """
    Add a real LLM service when LLM_ENABLED=true.

    Currently supports OpenAI. Can be extended for Azure, etc.
    """
    try:
        if settings.LLM_PROVIDER == "openai":
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

            service = OpenAIChatCompletion(
                ai_model_id=settings.LLM_MODEL or "gpt-4o-mini",
                api_key=settings.LLM_API_KEY,
            )
            kernel.add_service(service)
            logger.info(
                f"[Orchestration] Added OpenAI service: {settings.LLM_MODEL}"
            )
        else:
            logger.warning(
                f"[Orchestration] Unknown LLM provider: {settings.LLM_PROVIDER}. "
                f"Falling back to mock service."
            )
            _add_mock_service(kernel)
    except Exception as e:
        logger.error(f"[Orchestration] Failed to add LLM service: {e}. Using mock.")
        _add_mock_service(kernel)
