from dataclasses import dataclass, field


@dataclass
class CodeLocation:
    """Represents a location in source code."""

    file_path: str
    line_number: int
    column: int = 0
    context: str = ""


@dataclass
class CodeSmell:
    """Represents a code smell or anti-pattern."""

    name: str
    severity: str  # low, medium, high, critical
    location: CodeLocation
    description: str
    recommendation: str = ""


@dataclass
class AnalysisResult:
    """Results from code analysis."""

    file_path: str
    unused_imports: list[str] = field(default_factory=list)
    unused_functions: list[str] = field(default_factory=list)
    unused_variables: list[str] = field(default_factory=list)
    dead_code_lines: list[int] = field(default_factory=list)
    code_smells: list[CodeSmell] = field(default_factory=list)
    complexity_score: int = 0


@dataclass
class DuplicatePattern:
    """Represents duplicate code pattern."""

    pattern_hash: str
    locations: list[CodeLocation]
    code_snippet: str
    similarity_score: float


@dataclass
class Conflict:
    """Represents a dependency version conflict."""

    package_name: str
    required_versions: list[str]
    conflicting_packages: list[str]


@dataclass
class SecurityIssue:
    """Represents a security vulnerability."""

    severity: str  # critical, high, medium, low
    cve_id: str = ""
    description: str = ""
    affected_package: str = ""


@dataclass
class DependencyReport:
    """Report on project dependencies."""

    total_dependencies: int
    unused_dependencies: list[str] = field(default_factory=list)
    outdated_dependencies: list[tuple[str, str, str]] = field(
        default_factory=list
    )  # (name, current, latest)
    conflicts: list[Conflict] = field(default_factory=list)
    security_issues: list[SecurityIssue] = field(default_factory=list)


@dataclass
class QueryProfile:
    """Profile of a database query."""

    query_text: str
    execution_time: float
    row_count: int
    has_index: bool
    is_n_plus_one: bool = False


@dataclass
class ProfileResult:
    """Performance profiling results."""

    endpoint: str
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    slow_queries: list[QueryProfile] = field(default_factory=list)
    blocking_calls: list[str] = field(default_factory=list)
    memory_usage: int = 0


@dataclass
class Vulnerability:
    """Security vulnerability."""

    severity: str  # critical, high, medium, low
    vulnerability_type: str
    location: CodeLocation
    description: str
    recommendation: str = ""


@dataclass
class SecurityReport:
    """Security scan report."""

    file_path: str
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    severity_counts: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class QueryOptimization:
    """Query optimization recommendation."""

    query_location: CodeLocation
    current_query: str
    optimized_query: str
    improvement_description: str


@dataclass
class OptimizationPlan:
    """Plan for code optimizations."""

    files_to_modify: list[str] = field(default_factory=list)
    code_to_remove: list[CodeLocation] = field(default_factory=list)
    queries_to_optimize: list[QueryOptimization] = field(default_factory=list)
    dependencies_to_remove: list[str] = field(default_factory=list)
    estimated_improvement: float = 0.0  # percentage
