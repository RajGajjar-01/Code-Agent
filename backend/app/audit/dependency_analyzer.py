import re
import tomli
from pathlib import Path

from app.audit.models import DependencyReport, Conflict
from app.audit.logger import audit_logger


class DependencyAnalyzer:
    """Analyzes project dependencies for issues."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = audit_logger
        self.pyproject_path = self.project_root / "pyproject.toml"

    def analyze_dependencies(self) -> DependencyReport:
        """
        Analyze project dependencies.

        Returns:
            DependencyReport with findings
        """
        try:
            self.logger.info("Analyzing dependencies")

            # Parse pyproject.toml
            dependencies = self._parse_pyproject()

            # Find unused dependencies
            unused = self.find_unused_packages()

            # Check for conflicts (basic check)
            conflicts = self.check_conflicts()

            report = DependencyReport(
                total_dependencies=len(dependencies),
                unused_dependencies=unused,
                conflicts=conflicts,
            )

            self.logger.info(
                f"Dependency analysis complete: {len(unused)} unused, "
                f"{len(conflicts)} conflicts"
            )

            return report

        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}", exc_info=True)
            raise

    def _parse_pyproject(self) -> list[str]:
        """Parse pyproject.toml and extract dependencies."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")

        with open(self.pyproject_path, "rb") as f:
            data = tomli.load(f)

        dependencies = data.get("project", {}).get("dependencies", [])

        # Extract package names (remove version constraints)
        package_names = []
        for dep in dependencies:
            # Handle different dependency formats
            if isinstance(dep, str):
                # Extract package name before version specifier
                match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                if match:
                    package_names.append(match.group(1))

        return package_names

    def find_unused_packages(self) -> list[str]:
        """
        Find packages that are declared but never imported.

        Returns:
            List of unused package names
        """
        try:
            # Get declared dependencies
            declared = set(self._parse_pyproject())

            # Scan Python files for imports
            imported = self._scan_imports()

            # Find unused (declared but not imported)
            # Note: Some packages have different import names than package names
            # This is a simplified check
            unused = []
            for pkg in declared:
                # Normalize package name for comparison
                import_name = pkg.lower().replace("-", "_")

                # Check if any import matches
                found = False
                for imp in imported:
                    if imp.lower().startswith(import_name):
                        found = True
                        break

                if not found:
                    # Some packages are dependencies of other packages
                    # or have different import names - be conservative
                    # Only flag if we're confident it's unused
                    if pkg not in ["setuptools", "wheel", "pip"]:
                        unused.append(pkg)

            return unused

        except Exception as e:
            self.logger.error(f"Error finding unused packages: {e}")
            return []

    def _scan_imports(self) -> set[str]:
        """Scan all Python files for import statements."""
        imports = set()

        # Scan app directory
        app_dir = self.project_root / "app"
        if app_dir.exists():
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find import statements
                    import_pattern = r"^\s*(?:from|import)\s+([a-zA-Z0-9_]+)"
                    for match in re.finditer(import_pattern, content, re.MULTILINE):
                        imports.add(match.group(1))

                except Exception as e:
                    self.logger.warning(f"Error scanning {py_file}: {e}")
                    continue

        return imports

    def check_conflicts(self) -> list[Conflict]:
        """
        Check for version conflicts in dependencies.

        Returns:
            List of conflicts found
        """
        # This is a simplified check
        # A full implementation would use a dependency resolver
        conflicts = []

        try:
            with open(self.pyproject_path, "rb") as f:
                data = tomli.load(f)

            dependencies = data.get("project", {}).get("dependencies", [])

            # Track version requirements per package
            requirements: dict[str, list[str]] = {}

            for dep in dependencies:
                if isinstance(dep, str):
                    # Parse package name and version
                    match = re.match(r"^([a-zA-Z0-9_-]+)(.*)$", dep)
                    if match:
                        pkg_name = match.group(1)
                        version_spec = match.group(2).strip()

                        if pkg_name not in requirements:
                            requirements[pkg_name] = []

                        if version_spec:
                            requirements[pkg_name].append(version_spec)

            # Check for conflicting version specs
            for pkg_name, specs in requirements.items():
                if len(specs) > 1:
                    # Multiple version specs for same package
                    conflict = Conflict(
                        package_name=pkg_name,
                        required_versions=specs,
                        conflicting_packages=[pkg_name],
                    )
                    conflicts.append(conflict)

        except Exception as e:
            self.logger.error(f"Error checking conflicts: {e}")

        return conflicts

    def suggest_updates(self) -> list[tuple[str, str, str]]:
        """
        Suggest dependency updates.

        Returns:
            List of (package, current_version, latest_version) tuples
        """
        # This would require querying PyPI API
        # Placeholder for now
        return []
