import ast
from pathlib import Path
from typing import Any

from app.audit.models import AnalysisResult, CodeLocation, CodeSmell
from app.audit.logger import audit_logger


class SymbolTable:
    """Tracks symbol definitions and usages in Python code."""

    def __init__(self):
        self.definitions: dict[str, CodeLocation] = {}
        self.usages: set[str] = set()
        self.imports: dict[str, CodeLocation] = {}
        self.functions: dict[str, CodeLocation] = {}
        self.classes: dict[str, CodeLocation] = {}
        self.variables: dict[str, CodeLocation] = {}

    def add_import(self, name: str, location: CodeLocation) -> None:
        """Add an import to the symbol table."""
        self.imports[name] = location
        self.definitions[name] = location

    def add_function(self, name: str, location: CodeLocation) -> None:
        """Add a function definition."""
        self.functions[name] = location
        self.definitions[name] = location

    def add_class(self, name: str, location: CodeLocation) -> None:
        """Add a class definition."""
        self.classes[name] = location
        self.definitions[name] = location

    def add_variable(self, name: str, location: CodeLocation) -> None:
        """Add a variable definition."""
        self.variables[name] = location
        self.definitions[name] = location

    def mark_used(self, name: str) -> None:
        """Mark a symbol as used."""
        self.usages.add(name)

    def get_unused_imports(self) -> list[str]:
        """Get list of unused imports."""
        return [name for name in self.imports if name not in self.usages]

    def get_unused_functions(self) -> list[str]:
        """Get list of unused functions."""
        return [name for name in self.functions if name not in self.usages]

    def get_unused_variables(self) -> list[str]:
        """Get list of unused variables."""
        return [name for name in self.variables if name not in self.usages]


class ASTVisitor(ast.NodeVisitor):
    """AST visitor for analyzing Python code."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbol_table = SymbolTable()
        self.current_scope: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            location = CodeLocation(
                file_path=self.file_path, line_number=node.lineno, column=node.col_offset
            )
            self.symbol_table.add_import(name, location)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            location = CodeLocation(
                file_path=self.file_path, line_number=node.lineno, column=node.col_offset
            )
            self.symbol_table.add_import(name, location)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Skip private functions (starting with _) and special methods
        if not node.name.startswith("_"):
            location = CodeLocation(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                context=node.name,
            )
            self.symbol_table.add_function(node.name, location)

        # Enter function scope
        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        if not node.name.startswith("_"):
            location = CodeLocation(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                context=node.name,
            )
            self.symbol_table.add_function(node.name, location)

        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        if not node.name.startswith("_"):
            location = CodeLocation(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                context=node.name,
            )
            self.symbol_table.add_class(node.name, location)

        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name reference."""
        # Mark as used if it's a load context (reading the variable)
        if isinstance(node.ctx, ast.Load):
            self.symbol_table.mark_used(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access."""
        # Mark the base object as used
        if isinstance(node.value, ast.Name):
            self.symbol_table.mark_used(node.value.id)
        self.generic_visit(node)


class CodeAnalyzer:
    """Analyzes Python code for unused elements and code smells."""

    def __init__(self):
        self.logger = audit_logger

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Analyze a Python file for unused code and issues.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            AnalysisResult containing findings
        """
        try:
            self.logger.info(f"Analyzing file: {file_path}")

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                self.logger.error(f"Syntax error in {file_path}: {e}")
                return AnalysisResult(
                    file_path=file_path,
                    code_smells=[
                        CodeSmell(
                            name="SyntaxError",
                            severity="critical",
                            location=CodeLocation(file_path, e.lineno or 0, e.offset or 0),
                            description=str(e),
                        )
                    ],
                )

            # Visit AST and build symbol table
            visitor = ASTVisitor(file_path)
            visitor.visit(tree)

            # Calculate complexity (simple metric: number of functions + classes)
            complexity = len(visitor.symbol_table.functions) + len(visitor.symbol_table.classes)

            # Build result
            result = AnalysisResult(
                file_path=file_path,
                unused_imports=visitor.symbol_table.get_unused_imports(),
                unused_functions=visitor.symbol_table.get_unused_functions(),
                unused_variables=visitor.symbol_table.get_unused_variables(),
                complexity_score=complexity,
            )

            self.logger.info(
                f"Analysis complete: {len(result.unused_imports)} unused imports, "
                f"{len(result.unused_functions)} unused functions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}", exc_info=True)
            raise

    def find_unused_imports(self, file_path: str) -> list[str]:
        """Find unused imports in a file."""
        result = self.analyze_file(file_path)
        return result.unused_imports

    def find_dead_code(self, file_path: str) -> list[CodeLocation]:
        """Find dead code in a file."""
        result = self.analyze_file(file_path)
        dead_code = []

        # Add unused functions as dead code
        for func_name in result.unused_functions:
            # We'd need to store locations in the result to return them here
            # For now, return empty list
            pass

        return dead_code

    def find_duplicates(self, directory: str) -> list[Any]:
        """Find duplicate code patterns in a directory."""
        from app.audit.models import DuplicatePattern
        import hashlib
        from collections import defaultdict

        # Store code blocks by their hash
        code_blocks: dict[str, list[CodeLocation]] = defaultdict(list)

        # Walk through directory
        dir_path = Path(directory)
        for py_file in dir_path.rglob("*.py"):
            if any(part.startswith(".") or part == "__pycache__" for part in py_file.parts):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(py_file))

                # Extract function bodies
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Get function body as string
                        func_lines = content.split("\n")[node.lineno - 1 : node.end_lineno]
                        func_body = "\n".join(func_lines)

                        # Normalize whitespace for comparison
                        normalized = " ".join(func_body.split())

                        # Create hash (MD5 is fine for non-security code fingerprinting)
                        code_hash = hashlib.md5(
                            normalized.encode(), usedforsecurity=False
                        ).hexdigest()

                        location = CodeLocation(
                            file_path=str(py_file), line_number=node.lineno, context=node.name
                        )
                        code_blocks[code_hash].append(location)

            except Exception as e:
                self.logger.warning(f"Error processing {py_file}: {e}")
                continue

        # Find duplicates (blocks that appear more than once)
        duplicates = []
        for code_hash, locations in code_blocks.items():
            if len(locations) > 1:
                # Get code snippet from first location
                first_loc = locations[0]
                try:
                    with open(first_loc.file_path, "r") as f:
                        lines = f.readlines()
                        snippet = "".join(
                            lines[first_loc.line_number - 1 : first_loc.line_number + 5]
                        )
                except Exception:
                    snippet = ""

                duplicate = DuplicatePattern(
                    pattern_hash=code_hash,
                    locations=locations,
                    code_snippet=snippet[:200],  # Limit snippet size
                    similarity_score=1.0,  # Exact match
                )
                duplicates.append(duplicate)

        self.logger.info(f"Found {len(duplicates)} duplicate code patterns")
        return duplicates
