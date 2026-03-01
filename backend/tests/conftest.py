"""Pytest configuration and fixtures."""

import pytest
from hypothesis import settings


# Configure hypothesis for property-based testing
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=10, deadline=None)
settings.load_profile("dev")


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return """
import os
import sys
import unused_module

def used_function():
    return "used"

def unused_function():
    return "unused"

class UsedClass:
    pass

class UnusedClass:
    pass

used_var = 42
unused_var = 100
"""


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a temporary Python file for testing."""
    file_path = tmp_path / "test_file.py"
    file_path.write_text("""
import os
import unused_import

def main():
    print(os.path.exists('.'))
    
def unused_function():
    pass
""")
    return file_path
