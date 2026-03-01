# WordPress MCP (Model Context Protocol) Integration Guide

## Overview

This document provides comprehensive instructions for integrating WordPress with the Model Context Protocol (MCP), enabling AI assistants to interact with WordPress sites through standardized interfaces.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). It enables AI agents to:

- Access external data sources securely
- Execute operations on behalf of users
- Maintain consistent interfaces across different tools
- Provide rich context for AI-powered workflows

## MCP Architecture

```
AI Client (Claude, Cursor, etc.)
    ↓ (MCP protocol over stdio/JSON-RPC)
Local MCP Proxy
    ↓ (HTTP/HTTPS with authentication)
WordPress MCP Server
    ↓ (WordPress REST API)
WordPress Core + Plugins
```

## Available WordPress MCP Solutions

### 1. WordPress.com Built-in MCP Server

**Best for**: WordPress.com hosted sites

**Features**:
- Built-in OAuth 2.1 authentication
- No additional software installation required
- Official support for Claude, ChatGPT, VS Code, Cursor
- Comprehensive tool access based on user roles

**Server URL**:
```
https://public-api.wordpress.com/wpcom/v2/mcp/v1
```

**Setup Steps**:
1. Enable MCP on your WordPress.com account at https://wordpress.com/me/mcp
2. Toggle "Allow MCP access"
3. Configure your AI client with the server URL
4. Complete OAuth 2.1 authorization flow in browser

**Supported Tools**:
- Content Authoring (create/edit posts and pages)
- Site Editor Context
- Site Settings (admin only)
- Site Statistics
- Site Users (admin only)
- Posts Search
- Post Details
- Comments Search (editor/shop manager)
- Plugins (admin only)

### 2. Self-Hosted WordPress MCP Plugin

**Best for**: Self-hosted WordPress installations

**Repository**: Available on MCP Market and GitHub

**Features**:
- Implements MCP server using WordPress REST API
- Streamable HTTP transport
- Integrates with `logiscape/mcp-sdk-php` package
- Exposes MCP endpoint at `wp-json/mcp/v1/mcp`

**Installation**:
1. Install the WordPress MCP plugin from WordPress.org or GitHub
2. Activate the plugin in WordPress admin
3. Configure authentication (Application Passwords recommended)
4. Add the MCP endpoint to your AI client configuration

**Endpoint**:
```
{your-wordpress-site}/wp-json/mcp/v1/mcp
```

### 3. Custom MCP Server (This Implementation)

**Best for**: Custom WordPress integrations with full control

**Features**:
- Direct WordPress REST API integration
- Async Python client using httpx
- LangChain/LangGraph tool integration
- Custom tool definitions for AI agents

**Architecture**:
```python
# Backend: FastAPI + WordPress Client
WordPressClient (httpx) → WordPress REST API

# Agent: LangGraph Tools
@tool decorators → WordPressClient methods

# Frontend: React + API Routes
User Interface → FastAPI → Agent → WordPress
```

## Our Implementation: WordPress Agent Tools

### Available Tools

Our backend implements the following MCP-compatible tools:

#### Pages Management
- `list_pages`: List all WordPress pages with filtering
- `get_page`: Retrieve specific page with content and ACF fields
- `create_page`: Create new pages with HTML content
- `update_page`: Update existing page content and metadata
- `delete_page`: Delete pages (with trash bypass option)

#### Posts Management
- `list_posts`: List all WordPress posts with filtering
- `create_post`: Create new blog posts
- `delete_post`: Delete posts (with trash bypass option)

#### Media Management
- `upload_media`: Upload files to WordPress media library

#### ACF (Advanced Custom Fields)
- `get_acf_fields`: Retrieve ACF field values for pages/posts
- `update_acf_fields`: Update ACF field values
- `list_acf_field_groups`: List all ACF field groups (requires ACF Pro)

#### Theme Management
- `list_themes`: List all installed themes
- `get_active_theme`: Get currently active theme details
- `create_theme_file`: Create/update theme files
- `read_theme_file`: Read theme file contents
- `activate_theme`: Activate a theme by slug

#### Site Information
- `get_site_info`: Get site name, description, and URL

### Tool Definition Format

Tools are defined in two formats:

1. **LangChain Tool Format** (`backend/app/agent/tools.py`):
```python
@tool
async def create_page(title: str, content: str, status: str = "publish") -> dict:
    """Create a new WordPress page with the given title and HTML content."""
    return await _client().create_page(title=title, content=content, status=status)
```

2. **OpenAI Function Format** (`backend/app/tools.py`):
```python
{
    "type": "function",
    "function": {
        "name": "create_page",
        "description": "Create a new page.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "status": {"type": "string", "enum": ["publish", "draft"]},
            },
            "required": ["title", "content"],
        },
    },
}
```

## Authentication Methods

### 1. WordPress Application Passwords (Recommended)

**Setup**:
1. Log in to WordPress admin
2. Navigate to Users → Profile
3. Scroll to "Application Passwords" section
4. Enter application name (e.g., "WordPress Agent")
5. Click "Add New Application Password"
6. Copy the generated password (shown only once)

**Configuration**:
```env
WP_BASE_URL=https://your-wordpress-site.com
WP_USERNAME=your-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

**Security Benefits**:
- Doesn't expose main WordPress password
- Can be revoked without changing main password
- Scoped to REST API access only
- Supports multiple applications

### 2. OAuth 2.1 (WordPress.com)

**Features**:
- PKCE (Proof Key for Code Exchange)
- Dynamic Client Registration
- Token Rotation
- No Client Secrets Required
- Browser-based authorization flow

**Flow**:
1. AI client initiates connection
2. Browser opens to WordPress.com authorization page
3. User logs in and grants access
4. Client receives secure access token
5. Token automatically refreshes

**Management**:
- View connected apps: https://wordpress.com/me/security/connected-applications
- Revoke access anytime
- Tokens expire automatically

### 3. JWT Tokens (Custom Implementation)

Our backend also supports JWT authentication for frontend-to-backend communication:

```python
# Generate JWT token
from app.core.security import create_access_token

access_token = create_access_token(data={"sub": user.email})
```

## Configuring AI Clients

### Claude Desktop

**Method 1: Official Connector** (WordPress.com only)
1. Open Claude Settings → Connectors
2. Click "Browse connectors"
3. Search for "WordPress.com"
4. Click + to connect
5. Complete OAuth authorization

**Method 2: Manual Configuration** (Self-hosted)
```json
{
  "mcpServers": {
    "wordpress": {
      "command": "node",
      "args": ["/path/to/wordpress-mcp-server"],
      "env": {
        "WP_URL": "https://your-site.com",
        "WP_USERNAME": "your-username",
        "WP_APP_PASSWORD": "your-app-password"
      }
    }
  }
}
```

### ChatGPT

1. Open ChatGPT Settings → Apps → Advanced settings
2. Enable Developer Mode
3. Click "Create app"
4. Enter:
   - Name: WordPress.com (or custom name)
   - URL: `https://public-api.wordpress.com/wpcom/v2/mcp/v1`
   - Check "I understand and want to continue"
5. Complete OAuth authorization
6. Select WordPress connector when starting new chat

### Cursor

1. Navigate to https://cursor.com/docs/context/mcp/directory
2. Search for "WordPress"
3. Click "+Add to Cursor"
4. Click "Install" in Cursor app
5. Complete OAuth authorization

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "github.copilot.chat.mcp.servers": {
    "wordpress": {
      "url": "https://your-wordpress-site.com/wp-json/mcp/v1/mcp",
      "auth": {
        "type": "basic",
        "username": "your-username",
        "password": "your-app-password"
      }
    }
  }
}
```

## Security Best Practices

### 1. Authentication
- ✅ Use Application Passwords instead of main WordPress password
- ✅ Use OAuth 2.1 for WordPress.com integrations
- ✅ Rotate credentials regularly
- ✅ Revoke unused application passwords
- ❌ Never commit credentials to version control

### 2. Authorization
- ✅ Implement role-based access control
- ✅ Validate user permissions before operations
- ✅ Use WordPress capabilities system
- ✅ Audit MCP tool access regularly

### 3. Data Protection
- ✅ Use HTTPS for all connections
- ✅ Validate and sanitize all inputs
- ✅ Implement rate limiting
- ✅ Log security-relevant events
- ❌ Never log sensitive data (passwords, tokens)

### 4. Network Security
- ✅ Use secure transport (HTTPS/TLS)
- ✅ Implement CORS properly
- ✅ Validate SSL certificates
- ✅ Use firewall rules to restrict access

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to WordPress MCP server

**Solutions**:
1. Verify WordPress REST API is accessible:
   ```bash
   curl https://your-site.com/wp-json/
   ```
2. Check Application Password is correct
3. Verify WordPress user has appropriate permissions
4. Check firewall/security plugin settings
5. Review WordPress error logs

### Authentication Failures

**Problem**: 401 Unauthorized errors

**Solutions**:
1. Regenerate Application Password
2. Verify username is correct (not email)
3. Check for spaces in Application Password
4. Ensure user has required capabilities
5. Verify WordPress REST API authentication is enabled

### Tool Execution Errors

**Problem**: MCP tools fail to execute

**Solutions**:
1. Check WordPress plugin dependencies (e.g., ACF for ACF tools)
2. Verify user has permissions for the operation
3. Review WordPress REST API logs
4. Check for plugin conflicts
5. Validate request parameters

### Performance Issues

**Problem**: Slow MCP tool responses

**Solutions**:
1. Enable WordPress object caching
2. Optimize database queries
3. Use CDN for media files
4. Implement request caching
5. Monitor WordPress performance

## Advanced Configuration

### Custom Tool Development

To add custom WordPress MCP tools:

1. **Add method to WordPressClient**:
```python
# backend/app/services/wordpress.py
async def custom_operation(self, param: str) -> dict:
    """Custom WordPress operation."""
    response = await self.client.get(f"{self.api_url}/custom/{param}")
    response.raise_for_status()
    return response.json()
```

2. **Create LangChain tool**:
```python
# backend/app/agent/tools.py
@tool
async def custom_tool(param: str) -> dict:
    """Description of custom tool for AI."""
    return await _client().custom_operation(param)
```

3. **Add to tool list**:
```python
ALL_TOOLS = [
    # ... existing tools
    custom_tool,
]
```

### Rate Limiting

Implement rate limiting for MCP tools:

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request):
    # ... implementation
```

### Monitoring and Logging

Configure structured logging for MCP operations:

```python
import logging
import structlog

logger = structlog.get_logger()

async def execute_tool(name: str, args: dict):
    logger.info("mcp_tool_execution", tool=name, args=args)
    try:
        result = await tool_function(**args)
        logger.info("mcp_tool_success", tool=name)
        return result
    except Exception as e:
        logger.error("mcp_tool_error", tool=name, error=str(e))
        raise
```

## Resources

### Official Documentation
- MCP Specification: https://modelcontextprotocol.io/docs/getting-started/intro
- WordPress REST API: https://developer.wordpress.org/rest-api/
- WordPress.com MCP: https://developer.wordpress.com/docs/mcp/

### Tools and Libraries
- MCP SDK PHP: https://github.com/logiscape/mcp-sdk-php
- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/

### Community
- MCP Market: https://mcpmarket.com/
- WordPress MCP Servers: https://mcpservers.org/
- Automattic MCP Servers: https://automattic.ai/mcp

## Support

For issues specific to:
- **WordPress.com MCP**: Contact WordPress.com support
- **Self-hosted MCP Plugin**: Check plugin documentation and GitHub issues
- **This Implementation**: Review backend logs and create GitHub issue

## Changelog

### Version 0.3.0
- Added comprehensive MCP tool suite
- Implemented ACF field management
- Added theme file operations
- Enhanced error handling

### Version 0.2.0
- Initial MCP-compatible tool definitions
- WordPress REST API client implementation
- LangChain tool integration

### Version 0.1.0
- Basic WordPress API integration
- Authentication setup
