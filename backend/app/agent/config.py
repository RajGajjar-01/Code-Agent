"""Agent configuration with validation."""

import logging
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class AgentConfig(BaseSettings):
    """Agent configuration with validation and environment variable support."""

    # LLM Provider
    llm_provider: Literal["groq", "glm5", "gemini"] = Field(
        default="groq",
        validation_alias=AliasChoices("LLM_PROVIDER", "AGENT_LLM_PROVIDER"),
    )
    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY", "AGENT_GROQ_API_KEY"),
    )
    zai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ZAI_API_KEY", "AGENT_ZAI_API_KEY"),
    )
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "AGENT_GOOGLE_API_KEY"),
    )

    # Model settings
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL", "AGENT_GROQ_MODEL"),
    )
    glm5_model: str = Field(
        default="glm-5",
        validation_alias=AliasChoices("GLM5_MODEL", "AGENT_GLM5_MODEL"),
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",  # Latest as of 2026
        validation_alias=AliasChoices("GEMINI_MODEL", "AGENT_GEMINI_MODEL"),
    )

    # Agent behavior
    recursion_limit: int = Field(
        default=25,
        validation_alias=AliasChoices("RECURSION_LIMIT", "AGENT_RECURSION_LIMIT"),
    )
    retry_attempts: int = Field(
        default=3,
        validation_alias=AliasChoices("RETRY_ATTEMPTS", "AGENT_RETRY_ATTEMPTS"),
    )

    # Circuit breaker
    circuit_breaker_threshold: int = Field(
        default=5,
        validation_alias=AliasChoices(
            "CIRCUIT_BREAKER_THRESHOLD", "AGENT_CIRCUIT_BREAKER_THRESHOLD"
        ),
    )
    circuit_breaker_timeout: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "CIRCUIT_BREAKER_TIMEOUT", "AGENT_CIRCUIT_BREAKER_TIMEOUT"
        ),
    )

    # Observability
    langsmith_tracing: bool = Field(
        default=False,
        validation_alias=AliasChoices("LANGSMITH_TRACING", "AGENT_LANGSMITH_TRACING"),
    )
    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "AGENT_LANGSMITH_API_KEY"),
    )
    langsmith_project: str = Field(
        default="wordpress-agent",
        validation_alias=AliasChoices("LANGSMITH_PROJECT", "AGENT_LANGSMITH_PROJECT"),
    )

    # State persistence
    checkpoint_db_path: str = Field(
        default="agent_state.db",
        validation_alias=AliasChoices("CHECKPOINT_DB_PATH", "AGENT_CHECKPOINT_DB_PATH"),
    )

    # WP-CLI
    wp_cli_path: str = Field(
        default="wp",
        validation_alias=AliasChoices("WP_CLI_PATH", "AGENT_WP_CLI_PATH"),
    )
    wp_cli_wp_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WP_CLI_WP_PATH", "AGENT_WP_CLI_WP_PATH"),
    )
    wp_cli_default_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WP_CLI_DEFAULT_URL", "AGENT_WP_CLI_DEFAULT_URL"),
    )
    wp_cli_allow_root: bool = Field(
        default=False,
        validation_alias=AliasChoices("WP_CLI_ALLOW_ROOT", "AGENT_WP_CLI_ALLOW_ROOT"),
    )

    model_config = {
        "case_sensitive": False,
    }

    def validate_provider_keys(self) -> None:
        """Ensure required API keys are present for the selected provider."""
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY required for groq provider"
            )
        elif self.llm_provider == "glm5" and not self.zai_api_key:
            raise ValueError(
                "ZAI_API_KEY required for glm5 provider"
            )
        elif self.llm_provider == "gemini" and not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY required for gemini provider"
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
