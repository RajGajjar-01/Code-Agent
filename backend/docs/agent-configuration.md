# Agent Configuration Guide

This document explains how to configure the WordPress Agent with different LLM providers and settings.

## Environment Variables

All agent configuration is done through environment variables with the `AGENT_` prefix.

### LLM Provider Selection

Choose your LLM provider by setting:

```bash
AGENT_LLM_PROVIDER=groq  # Options: groq, glm5, gemini
```

### Provider-Specific Configuration

#### Groq (Default)
Fast inference with Llama 3.3 70B:

```bash
GROQ_API_KEY=gsk_your_api_key_here
AGENT_GROQ_MODEL=llama-3.3-70b-versatile
```

Get your API key from: https://console.groq.com/

#### Z.AI GLM-5
Optimized for agentic tasks and long-horizon planning:

```bash
ZAI_API_KEY=your_zai_api_key_here
AGENT_GLM5_MODEL=glm-5
```

Get your API key from: https://z.ai/

#### Google Gemini 2.5 Flash
Advanced reasoning with Google's latest model:

```bash
GOOGLE_API_KEY=your_google_api_key_here
AGENT_GEMINI_MODEL=gemini-2.5-flash
```

Get your API key from: https://makersuite.google.com/app/apikey

### Agent Behavior Settings

Control how the agent executes:

```bash
# Maximum number of execution steps before termination
AGENT_RECURSION_LIMIT=25

# Number of recent tool calls to check for duplicates
AGENT_DUPLICATE_WINDOW=3

# Number of retry attempts for failed API calls
AGENT_RETRY_ATTEMPTS=3
```

### Circuit Breaker Settings

Prevent cascading failures:

```bash
# Number of failures before opening the circuit
AGENT_CIRCUIT_BREAKER_THRESHOLD=5

# Seconds to wait before testing recovery
AGENT_CIRCUIT_BREAKER_TIMEOUT=60
```

### Observability (Optional)

Enable LangSmith tracing for debugging:

```bash
AGENT_LANGSMITH_TRACING=true
AGENT_LANGSMITH_API_KEY=your_langsmith_api_key_here
AGENT_LANGSMITH_PROJECT=wordpress-agent
```

Get your LangSmith API key from: https://smith.langchain.com/

### State Persistence

Configure checkpoint storage:

```bash
AGENT_CHECKPOINT_DB_PATH=agent_state.db
```

## Frontend Model Selection

Users can select their preferred model from the frontend UI:

1. Click the model selector dropdown in the header
2. Choose from:
   - **Groq (Llama 3.3 70B)**: Fast inference, great for general tasks
   - **GLM-5 (Z.AI)**: Optimized for agentic tasks & long-horizon planning
   - **Gemini 2.5 Flash**: Google's latest model with advanced reasoning

The selection is persisted in localStorage and sent with each chat message.

## Architecture Features

### Infinite Loop Prevention
- **Recursion Limit**: Enforces maximum execution steps
- **Duplicate Detection**: Prevents identical tool calls within a sliding window
- **Remaining Steps Warning**: Alerts the LLM when steps are running low

### Reliability Patterns
- **Circuit Breaker**: Fails fast when external services are down
- **Retry Logic**: Exponential backoff for transient failures
- **Smart Retry**: No retry on 4xx errors, retry on 5xx and network errors

### Error Handling
- **Structured Errors**: Categorized error responses with suggestions
- **Error Context**: Full context about what was being attempted
- **LLM Feedback**: Errors are returned to the LLM for reasoning

### Observability
- **Execution Summary**: Total steps, tool calls, execution time
- **Tool Call Logging**: Timestamp, arguments, results, duration
- **Pattern Detection**: Identifies repeated tool calls and failures
- **LangSmith Integration**: Optional tracing for debugging

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Set your API key for your chosen provider:
   ```bash
   # For Groq (default)
   GROQ_API_KEY=gsk_your_actual_key_here
   
   # Or for GLM-5
   ZAI_API_KEY=your_actual_key_here
   
   # Or for Gemini
   GOOGLE_API_KEY=your_actual_key_here
   ```

3. Optionally adjust behavior settings (defaults are production-ready)

4. Start the backend:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

5. The agent will automatically use your configuration!

## Troubleshooting

### "API key required" error
Make sure you've set the API key for your selected provider:
- `GROQ_API_KEY` for groq
- `ZAI_API_KEY` for glm5
- `GOOGLE_API_KEY` for gemini

### Circuit breaker is open
The external service is experiencing issues. Wait for the timeout period (default 60s) or check the service status.

### Duplicate tool call detected
The agent is stuck in a loop. The system will prevent the duplicate and suggest alternative approaches to the LLM.

### Recursion limit reached
The task is too complex for the current limit. Increase `AGENT_RECURSION_LIMIT` or break the task into smaller steps.

## Best Practices

1. **Start with defaults**: The default settings are production-ready
2. **Monitor execution summaries**: Check logs for duplicate detections and circuit breaker trips
3. **Enable LangSmith for debugging**: Helpful when troubleshooting complex issues
4. **Use appropriate models**: 
   - Groq for speed
   - GLM-5 for complex agentic tasks
   - Gemini for advanced reasoning
5. **Set reasonable limits**: Balance between allowing complex tasks and preventing runaway execution

## API Reference

See the [Agent Architecture Design Document](../../.kiro/specs/agent-architecture-improvements/design.md) for detailed technical specifications.
