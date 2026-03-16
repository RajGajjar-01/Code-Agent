"""LLM provider factory for creating language model instances."""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.agent.config import AgentConfig

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM instances based on configuration."""

    @staticmethod
    def create(config: AgentConfig) -> BaseChatModel:
        """
        Create LLM instance based on configuration.

        Args:
            config: Agent configuration with provider settings

        Returns:
            Configured LLM instance

        Raises:
            ValueError: If provider is unknown or configuration is invalid
        """
        logger.info(f"Creating LLM provider: {config.llm_provider}")

        if config.llm_provider == "groq":
            return ChatGroq(
                api_key=config.groq_api_key,
                model=config.groq_model,
                temperature=0,
            )

        elif config.llm_provider == "glm5":
            # GLM-5 uses OpenAI-compatible API
            logger.info(f"Using GLM-4.7-flash model: {config.glm5_model}")
            return ChatOpenAI(
                base_url="https://api.z.ai/api/paas/v4",
                api_key=config.zai_api_key,
                model=config.glm5_model,
                temperature=0,
            )

        elif config.llm_provider == "gemini":
            # Gemini 2.5 Flash - latest recommended model for general tasks
            logger.info(f"Using Gemini model: {config.gemini_model}")
            return ChatGoogleGenerativeAI(
                model=config.gemini_model,
                google_api_key=config.google_api_key,
                temperature=0,
            )

        else:
            raise ValueError(
                f"Unknown provider: {config.llm_provider}. "
                f"Supported providers: groq, glm5, gemini"
            )
