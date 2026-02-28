# Design Document

## Overview

This design outlines a comprehensive audit and optimization strategy for the FastAPI-based WordPress Agent backend. The system currently integrates WordPress REST API, Google Drive, JWT authentication, LangGraph AI agents, and PostgreSQL database. The audit will systematically review every file, eliminate dead code, optimize performance, enhance error handling, validate WordPress endpoints, and generate comprehensive documentation.

The optimization focuses on three key pillars:
1. **Performance**: Reduce response times by 30%+ through async optimization, database query improvements, and dependency cleanup
2. **Robustness**: Implement comprehensive error handling, validation, and retry logic
3. **Maintainability**: Remove dead code, improve type hints, add documentation, and validate all integrations

## Architecture

### Current System Architecture

```
┌─────────────────┐
│  React Frontend │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌──────────────────────────────┐  │
│  │  API Routes Layer            │  │
│  │  - /api/auth                 │  │
│  │  - /api/chat                 │  │
│  │  - /api/drive                │  │
│  │  - /api/scrape               │  │
│  │  - /api/ide                  │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │  Services Layer              │  │
│  │  - ChatService               │  │
│  │  - ConversationService       │  │
│  │  - TokenService              │  │
│  │  - GoogleDriveService        │  │
│  │  - WordPressClient           │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │  Agent Layer (LangGraph)     │  │
│  │  - State Management          │  │
│  │  - Tool Execution            │  │
│  │  - Graph Orchestration       │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │  Data Layer                  │  │
│  │  - SQLAlchemy Models         │  │
│  │  - Alembic Migrations        │  │
│  └──────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌──────────────┐
│PostgreSQL│      │External APIs │
│ Database │      │- WordPress   │
└──────────┘      │- Google Drive│
                  │- Groq LLM    │
                  └──────────────┘
```

### Audit Process Flow

```
┌──────────────────┐
│  File Discovery  │
│  - Scan all .py  │
│  - Build dep tree│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Static Analysis │
│  - Unused imports│
│  - Dead code     │
│  - Type coverage │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Dependency Audit│
│  - Unused pkgs   │
│  - Version check │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Performance     │
│  - Async patterns│
│  - DB queries    │
│  - Bottlenecks   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Security Scan   │
│  - Input valid.  │
│  - SQL injection │
│  - Secret leaks  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  WP Endpoint Val.│
│  - Test all APIs │
│  - Document      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Generate Docs   │
│  - endpoints.md  │
│  - mcp.md        │
└──────────────────┘
```

## Components and Interfaces

### 1. Code Audit Module

**Purpose**: Scan all Python files to identify unused code, imports, and optimization opportunities.

**Interface**:
```python
class CodeAuditor:
    async def scan_directory(self, path: str) -> AuditReport
    async def find_unused_imports(self, file_path: str) -> list[str]
    async def find_dead_code(self, file_path: str) -> list[CodeBlock]
    async def check_type_coverage(self, file_path: str) -> TypeCoverageReport
    async def find_duplicate_code(self, files: list[str]) -> list[DuplicatePattern]
```

**Key Responsibilities**:
- Parse Python AST to identify unused imports
- Detect unreachable code paths
- Find functions/classes with no references
- Identify duplicate code patterns
- Calculate type hint coverage

### 2. Dependency Optimizer

**Purpose**: Analyze and optimize project dependencies.

**Interface**:
```python
class DependencyOptimizer:
    async def scan_imports(self) -> dict[str, list[str]]
    async def find_unused_dependencies(self) -> list[str]
    async def check_version_conflicts(self) -> list[VersionConflict]
    async def suggest_updates(self) -> list[DependencyUpdate]
```

**Key Responsibilities**:
- Map all import statements to dependencies
- Identify packages in pyproject.toml not used in code
- Detect version conflicts
- Suggest compatible version updates

### 3. Performance Analyzer

**Purpose**: Identify and fix performance bottlenecks.

**Interface**:
```python
class PerformanceAnalyzer:
    async def analyze_async_patterns(self) -> list[AsyncIssue]
    async def analyze_database_queries(self) -> list[QueryOptimization]
    async def find_blocking_calls(self) -> list[BlockingCall]
    async def measure_endpoint_latency(self) -> dict[str, float]
```

**Key Responsibilities**:
- Detect blocking I/O in async functions
- Identify N+1 query problems
- Find missing database indexes
- Measure endpoint response times
- Detect inefficient serialization

### 4. Error Handler Enhancer

**Purpose**: Improve error handling throughout the codebase.

**Interface**:
```python
class ErrorHandlerEnhancer:
    async def find_unhandled_exceptions(self) -> list[ExceptionSite]
    async def add_try_catch_blocks(self, file_path: str) -> None
    async def implement_retry_logic(self, function: str) -> None
    async def add_validation(self, endpoint: str) -> None
```

**Key Responsibilities**:
- Identify functions without exception handling
- Add appropriate try-catch blocks
- Implement retry logic for external API calls
- Add input validation to all endpoints
- Ensure proper error logging

### 5. Security Auditor

**Purpose**: Identify and fix security vulnerabilities.

**Interface**:
```python
class SecurityAuditor:
    async def scan_sql_injection(self) -> list[SQLInjectionRisk]
    async def check_password_hashing(self) -> list[SecurityIssue]
    async def find_secret_leaks(self) -> list[SecretLeak]
    async def validate_input_sanitization(self) -> list[ValidationIssue]
```

**Key Responsibilities**:
- Detect SQL injection vulnerabilities
- Verify password hashing implementation
- Find hardcoded secrets or API keys
- Ensure all user inputs are validated
- Check JWT token security

### 6. WordPress Endpoint Validator

**Purpose**: Validate all WordPress REST API endpoints and generate documentation.

**Interface**:
```python
class WordPressEndpointValidator:
    async def validate_endpoint(self, endpoint: str, method: str) -> ValidationResult
    async def test_all_endpoints(self) -> dict[str, ValidationResult]
    async def generate_endpoints_doc(self) -> str
    async def check_acf_availability(self) -> ACFStatus
```

**Key Responsibilities**:
- Test each WordPress REST API endpoint
- Verify expected response formats
- Document all endpoints with parameters
- Check ACF Pro REST API availability
- Generate endpoints.md file

### 7. MCP Documentation Generator

**Purpose**: Generate comprehensive MCP documentation for WordPress integration.

**Interface**:
```python
class MCPDocGenerator:
    async def generate_mcp_doc(self) -> str
    async def document_tools(self) -> list[ToolDoc]
    async def create_examples(self) -> list[CodeExample]
    async def add_troubleshooting(self) -> list[TroubleshootingItem]
```

**Key Responsibilities**:
- Document MCP server setup
- List all available WordPress tools
- Provide usage examples
- Include troubleshooting guide
- Generate mcp.md file

## Data Models

### AuditReport
```python
@dataclass
class AuditReport:
    file_path: str
    unused_imports: list[str]
    dead_code_blocks: list[CodeBlock]
    type_coverage: float
    issues: list[Issue]
    suggestions: list[Suggestion]
```

### CodeBlock
```python
@dataclass
class CodeBlock:
    file_path: str
    line_start: int
    line_end: int
    code_type: str  # function, class, variable
    name: str
    reason: str  # why it's considered dead
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    endpoint: str
    method: str
    status: str  # success, failed, not_found
    response_time: float
    response_format: dict
    error_message: Optional[str]
```

### ToolDoc
```python
@dataclass
class ToolDoc:
    name: str
    description: str
    parameters: dict[str, ParameterSpec]
    return_type: str
    example: str
```

### OptimizationMetrics
```python
@dataclass
class OptimizationMetrics:
    files_scanned: int
    lines_removed: int
    dependencies_removed: int
    performance_improvement: float  # percentage
    errors_fixed: int
    security_issues_fixed: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Code removal preserves functionality
*For any* code removal operation, when dead code is removed from a file, all existing tests should continue to pass without modification
**Validates: Requirements 1.4**

### Property 2: Dependency removal maintains imports
*For any* dependency removed from pyproject.toml, no import statement in the codebase should reference that package
**Validates: Requirements 2.2**

### Property 3: Async optimization maintains correctness
*For any* function converted to use async/await patterns, the function's output for the same inputs should remain identical to the original implementation
**Validates: Requirements 3.3**

### Property 4: Error handling preserves success paths
*For any* function where error handling is added, successful execution paths should produce identical results to the original implementation
**Validates: Requirements 4.1**

### Property 5: Input validation rejects invalid data
*For any* API endpoint with input validation, when invalid data is submitted, the endpoint should return a 422 status code with field-level error details
**Validates: Requirements 4.4**

### Property 6: WordPress endpoint validation completeness
*For any* WordPress REST API method in WordPressClient, there should exist a corresponding validation test that verifies the endpoint's availability and response format
**Validates: Requirements 11.1**

### Property 7: Documentation accuracy
*For any* WordPress endpoint documented in endpoints.md, the documented parameters and response format should match the actual API behavior
**Validates: Requirements 11.4**

### Property 8: MCP tool documentation completeness
*For any* tool defined in TOOL_DEFINITIONS, there should exist corresponding documentation in mcp.md with parameters and usage examples
**Validates: Requirements 12.3**

## Error Handling

### 1. File System Errors
- **Scenario**: File not found, permission denied during audit
- **Handling**: Log error, skip file, continue with remaining files
- **Recovery**: Generate partial report with list of skipped files

### 2. Dependency Resolution Errors
- **Scenario**: Cannot determine if dependency is used
- **Handling**: Mark as "uncertain", require manual review
- **Recovery**: Include in report with recommendation to keep

### 3. WordPress API Errors
- **Scenario**: WordPress site unreachable, authentication fails
- **Handling**: Retry with exponential backoff (3 attempts)
- **Recovery**: Document endpoint as "unable to validate", provide manual testing instructions

### 4. Database Migration Errors
- **Scenario**: Migration file has syntax errors
- **Handling**: Report error, do not attempt to fix automatically
- **Recovery**: Flag for manual review with error details

### 5. Code Parsing Errors
- **Scenario**: Python file has syntax errors
- **Handling**: Log error, skip optimization for that file
- **Recovery**: Include in report as "requires manual fix"

### 6. Test Failures After Optimization
- **Scenario**: Tests fail after code removal
- **Handling**: Rollback changes to that specific file
- **Recovery**: Mark code as "cannot be safely removed"

## Testing Strategy

### Unit Testing Approach

Unit tests will verify individual audit components work correctly:

- **CodeAuditor tests**: Verify unused import detection with sample files
- **DependencyOptimizer tests**: Test dependency mapping logic
- **PerformanceAnalyzer tests**: Validate async pattern detection
- **SecurityAuditor tests**: Test vulnerability detection patterns
- **WordPressEndpointValidator tests**: Mock WordPress API responses
- **MCPDocGenerator tests**: Verify documentation generation format

### Property-Based Testing Approach

Property-based tests will verify universal correctness properties using **Hypothesis** library (Python's leading PBT framework):

- Configure each property test to run minimum 100 iterations
- Each property test must reference its design document property using format: `**Feature: backend-audit-optimization, Property {number}: {property_text}**`
- Each correctness property must be implemented by a single property-based test

**Property Test Examples**:

1. **Code Removal Preservation**: Generate random Python files with unused code, remove it, verify AST equivalence for used code
2. **Dependency Consistency**: Generate random import sets, remove dependencies, verify no broken imports
3. **Async Correctness**: Generate random sync functions, convert to async, verify output equivalence
4. **Validation Rejection**: Generate random invalid payloads, verify all return 422 with details
5. **Documentation Accuracy**: Generate random endpoint configurations, verify documentation matches implementation

### Integration Testing

- Test complete audit workflow end-to-end
- Verify WordPress endpoint validation against real WordPress instance
- Test MCP documentation generation produces valid markdown
- Verify optimization metrics are calculated correctly

### Testing Tools

- **pytest**: Test runner and framework
- **pytest-asyncio**: Async test support
- **hypothesis**: Property-based testing
- **pytest-cov**: Code coverage measurement
- **httpx**: HTTP client for API testing
- **pytest-mock**: Mocking support

## Implementation Notes

### Phase 1: Discovery and Analysis
1. Scan all Python files in backend/app
2. Build dependency graph
3. Identify unused code and imports
4. Generate initial audit report

### Phase 2: Dependency Optimization
1. Map all imports to dependencies
2. Identify unused packages
3. Check for version conflicts
4. Update pyproject.toml

### Phase 3: Performance Optimization
1. Analyze async patterns
2. Optimize database queries
3. Add missing indexes
4. Reduce serialization overhead

### Phase 4: Error Handling Enhancement
1. Add try-catch blocks
2. Implement retry logic
3. Add input validation
4. Improve error logging

### Phase 5: Security Hardening
1. Fix SQL injection risks
2. Verify password hashing
3. Remove secret leaks
4. Add input sanitization

### Phase 6: WordPress Validation
1. Test all WordPress endpoints
2. Verify ACF availability
3. Generate endpoints.md
4. Document fallback behaviors

### Phase 7: MCP Documentation
1. Document MCP setup
2. List all tools
3. Create usage examples
4. Add troubleshooting guide
5. Generate mcp.md

### Phase 8: Verification
1. Run all tests
2. Measure performance improvements
3. Verify zero errors
4. Generate final metrics report

## WordPress REST API Endpoints

The system integrates with the following WordPress REST API v2 endpoints:

### Pages
- `GET /wp/v2/pages` - List pages
- `GET /wp/v2/pages/{id}` - Get single page
- `POST /wp/v2/pages` - Create page
- `POST /wp/v2/pages/{id}` - Update page
- `DELETE /wp/v2/pages/{id}` - Delete page

### Posts
- `GET /wp/v2/posts` - List posts
- `POST /wp/v2/posts` - Create post
- `DELETE /wp/v2/posts/{id}` - Delete post

### Media
- `POST /wp/v2/media` - Upload media file

### Themes
- `GET /wp/v2/themes` - List themes
- `GET /wp/v2/themes?status=active` - Get active theme
- `POST /wp/v2/themes/{slug}` - Activate theme

### ACF (Advanced Custom Fields)
- `GET /acf/v3/field-groups` - List ACF field groups (requires ACF Pro)
- ACF fields embedded in page/post responses

### Site Info
- `GET /wp-json` - Get site information

All endpoints require HTTP Basic Authentication using WordPress application password.

## MCP Integration

The system uses Model Context Protocol (MCP) to expose WordPress operations as tools for AI agents. The MCP server provides:

- Tool definitions for all WordPress operations
- Async tool execution
- Error handling and retry logic
- Response formatting for LLM consumption

Tools are defined in `backend/app/tools.py` and executed via `execute_tool()` function.
