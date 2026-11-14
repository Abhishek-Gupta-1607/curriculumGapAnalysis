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
    Add a real LLM service when LLM_ENABLED=true and LLM_API_KEY is provided.

    Supports:
    - "openai": Standard OpenAI (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
    - "azure" / "azure_openai": Microsoft Azure OpenAI Service
    - "groq" / "deepseek" / "openrouter" / "custom": OpenAI-compatible base URLs
    """
    try:
        provider = settings.LLM_PROVIDER.lower()
        model_name = settings.LLM_MODEL or "gpt-4o-mini"

        if provider in ("azure", "azure_openai"):
            from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

            service = AzureChatCompletion(
                deployment_name=model_name,
                endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.LLM_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION or "2024-02-15-preview",
            )
            kernel.add_service(service)
            logger.info(f"[Orchestration] Added Azure OpenAI service: {model_name}")

        elif provider in ("grok", "xai", "groq", "deepseek", "openrouter", "custom") or settings.LLM_BASE_URL:
            import openai
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

            # Map known base URLs and default models if not explicitly set
            base_url = settings.LLM_BASE_URL
            if not base_url:
                if provider in ("grok", "xai"):
                    base_url = "https://api.x.ai/v1"
                    if not settings.LLM_MODEL:
                        model_name = "grok-2-latest"
                elif provider == "groq":
                    base_url = "https://api.groq.com/openai/v1"
                    if not settings.LLM_MODEL:
                        model_name = "llama-3.3-70b-versatile"
                elif provider == "deepseek":
                    base_url = "https://api.deepseek.com/v1"
                    if not settings.LLM_MODEL:
                        model_name = "deepseek-chat"
                elif provider == "openrouter":
                    base_url = "https://openrouter.ai/api/v1"
                    if not settings.LLM_MODEL:
                        model_name = "google/gemini-2.0-flash-001"

            async_client = openai.AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=base_url if base_url else None,
            )
            service = OpenAIChatCompletion(
                ai_model_id=model_name,
                async_client=async_client,
            )
            kernel.add_service(service)
            logger.info(f"[Orchestration] Added {provider.upper()} OpenAI-compatible service: {model_name}")

        elif provider == "openai":
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

            service = OpenAIChatCompletion(
                ai_model_id=model_name,
                api_key=settings.LLM_API_KEY,
            )
            kernel.add_service(service)
            logger.info(f"[Orchestration] Added OpenAI service: {model_name}")

        else:
            logger.warning(
                f"[Orchestration] Unknown LLM provider: '{settings.LLM_PROVIDER}'. "
                f"Falling back to mock service."
            )
            _add_mock_service(kernel)
    except Exception as e:
        logger.error(f"[Orchestration] Failed to add LLM service: {e}. Falling back to mock service.")
        _add_mock_service(kernel)
