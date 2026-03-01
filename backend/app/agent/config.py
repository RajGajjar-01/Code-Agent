"""Agent configuration with validation."""

import logging
from typing import Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class AgentConfig(BaseSettings):
    """Agent configuration with validation and environment variable support."""

    # LLM Provider
    llm_provider: Literal["groq", "glm5", "gemini"] = "groq"
    groq_api_key: str | None = None
    zai_api_key: str | None = None
    google_api_key: str | None = None

    # Model settings
    groq_model: str = "llama-3.3-70b-versatile"
    glm5_model: str = "glm-5"
    gemini_model: str = "gemini-2.5-flash"  # Latest as of 2026

    # Agent behavior
    recursion_limit: int = 25
    retry_attempts: int = 3

    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # Observability
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "wordpress-agent"

    # State persistence
    checkpoint_db_path: str = "agent_state.db"

    model_config = {
        "env_prefix": "AGENT_",
        "case_sensitive": False,
    }

    def validate_provider_keys(self) -> None:
        """Ensure required API keys are present for the selected provider."""
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY or AGENT_GROQ_API_KEY required for groq provider"
            )
        elif self.llm_provider == "glm5" and not self.zai_api_key:
            raise ValueError(
                "ZAI_API_KEY or AGENT_ZAI_API_KEY required for glm5 provider"
            )
        elif self.llm_provider == "gemini" and not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY or AGENT_GOOGLE_API_KEY required for gemini provider"
            )

    def validate_config_values(self) -> None:
        """Validate configuration values and log warnings for invalid ones."""
        if self.recursion_limit < 1:
            logger.warning(
                f"Invalid recursion_limit={self.recursion_limit}, using default 25"
            )
            self.recursion_limit = 25

        if self.retry_attempts < 1:
            logger.warning(
                f"Invalid retry_attempts={self.retry_attempts}, using default 3"
            )
            self.retry_attempts = 3

        if self.circuit_breaker_threshold < 1:
            logger.warning(
                f"Invalid circuit_breaker_threshold={self.circuit_breaker_threshold}, using default 5"
            )
            self.circuit_breaker_threshold = 5

        if self.circuit_breaker_timeout < 1:
            logger.warning(
                f"Invalid circuit_breaker_timeout={self.circuit_breaker_timeout}, using default 60"
            )
            self.circuit_breaker_timeout = 60

    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        self.validate_config_values()
        self.validate_provider_keys()


# Global configuration instance
_config: AgentConfig | None = None


def get_agent_config() -> AgentConfig:
    """Get or create the global agent configuration instance."""
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config


def reset_agent_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None
