"""Quick audit script to analyze the backend codebase."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.audit.code_analyzer import CodeAnalyzer
from app.audit.dependency_analyzer import DependencyAnalyzer


def main():
    print("=" * 80)
    print("BACKEND AUDIT REPORT")
    print("=" * 80)
    
    # Analyze code
    print("\n1. CODE ANALYSIS")
    print("-" * 80)
    
    analyzer = CodeAnalyzer()
    app_dir = Path("app")
    
    total_unused_imports = 0
    total_unused_functions = 0
    files_with_issues = []
    
    for py_file in app_dir.rglob("*.py"):
        if '__pycache__' in str(py_file) or 'audit' in str(py_file):
            continue
        
        try:
            result = analyzer.analyze_file(str(py_file))
            if result.unused_imports or result.unused_functions:
                files_with_issues.append((str(py_file), result))
                total_unused_imports += len(result.unused_imports)
                total_unused_functions += len(result.unused_functions)
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}")
    
    print(f"\nFiles analyzed: {len(list(app_dir.rglob('*.py')))}")
    print(f"Files with issues: {len(files_with_issues)}")
    print(f"Total unused imports: {total_unused_imports}")
    print(f"Total unused functions: {total_unused_functions}")
    
    if files_with_issues:
        print("\nTop 5 files with most issues:")
        sorted_files = sorted(
            files_with_issues,
            key=lambda x: len(x[1].unused_imports) + len(x[1].unused_functions),
            reverse=True
        )[:5]
        
        for file_path, result in sorted_files:
            print(f"\n  {file_path}:")
            if result.unused_imports:
                print(f"    Unused imports: {', '.join(result.unused_imports[:5])}")
            if result.unused_functions:
                print(f"    Unused functions: {', '.join(result.unused_functions[:5])}")
    
    # Analyze dependencies
    print("\n\n2. DEPENDENCY ANALYSIS")
    print("-" * 80)
    
    dep_analyzer = DependencyAnalyzer(".")
    try:
        dep_report = dep_analyzer.analyze_dependencies()
        print(f"\nTotal dependencies: {dep_report.total_dependencies}")
        print(f"Potentially unused: {len(dep_report.unused_dependencies)}")
        
        if dep_report.unused_dependencies:
            print(f"\nPotentially unused dependencies:")
            for dep in dep_report.unused_dependencies[:10]:
                print(f"  - {dep}")
        
        if dep_report.conflicts:
            print(f"\nVersion conflicts: {len(dep_report.conflicts)}")
            for conflict in dep_report.conflicts:
                print(f"  - {conflict.package_name}: {conflict.required_versions}")
    except Exception as e:
        print(f"Error analyzing dependencies: {e}")
    
    # Check duplicates
    print("\n\n3. DUPLICATE CODE DETECTION")
    print("-" * 80)
    
    try:
        duplicates = analyzer.find_duplicates("app")
        print(f"\nDuplicate code patterns found: {len(duplicates)}")
        
        if duplicates:
            print("\nTop 3 duplicates:")
            for i, dup in enumerate(duplicates[:3], 1):
                print(f"\n  {i}. Found in {len(dup.locations)} locations:")
                for loc in dup.locations[:3]:
                    print(f"     - {loc.file_path}:{loc.line_number} ({loc.context})")
    except Exception as e:
        print(f"Error detecting duplicates: {e}")
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
