import ast
import os
from pathlib import Path


def remove_module_docstring(file_path):
    """Remove module-level docstring from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        # Check if first statement is a docstring
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            
            # Get the docstring node
            docstring_node = tree.body[0]
            
            # Find the line range of the docstring
            start_line = docstring_node.lineno - 1  # 0-indexed
            end_line = docstring_node.end_lineno  # 1-indexed, so this is correct
            
            # Split content into lines
            lines = content.split('\n')
            
            # Remove docstring lines
            new_lines = lines[:start_line] + lines[end_line:]
            
            # Remove leading empty lines
            while new_lines and not new_lines[0].strip():
                new_lines.pop(0)
            
            new_content = '\n'.join(new_lines)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Removed docstring from: {file_path}")
            return True
    except:
        pass
    
    return False


def main():
    app_dir = Path("app")
    count = 0
    
    for py_file in app_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        
        if remove_module_docstring(py_file):
            count += 1
    
    print(f"\nTotal files processed: {count}")


if __name__ == "__main__":
    main()
