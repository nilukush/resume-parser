#!/usr/bin/env python3
"""
Structure validation script for Task 4.

This script verifies that all required files exist and have the expected structure
without requiring all dependencies to be installed.
"""

import ast
import sys
from pathlib import Path


def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"  [OK] {filepath}")
        return True
    else:
        print(f"  [MISSING] {filepath}")
        return False


def validate_python_syntax(filepath: str) -> bool:
    """Validate Python file syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f"  [SYNTAX OK] {filepath}")
        return True
    except SyntaxError as e:
        print(f"  [SYNTAX ERROR] {filepath}: {e}")
        return False


def validate_class_exists(filepath: str, class_name: str) -> bool:
    """Check if a class exists in a Python file."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                print(f"  [CLASS FOUND] {class_name} in {filepath}")
                return True
        print(f"  [CLASS NOT FOUND] {class_name} in {filepath}")
        return False
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
        return False


def validate_function_exists(filepath: str, function_name: str) -> bool:
    """Check if a function exists in a Python file."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                print(f"  [FUNCTION FOUND] {function_name} in {filepath}")
                return True
        print(f"  [FUNCTION NOT FOUND] {function_name} in {filepath}")
        return False
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")
        return False


def main():
    """Run all validation checks."""
    base_path = Path("/Users/nileshkumar/gh/resume-parser/backend")
    all_passed = True

    print("=" * 60)
    print("Task 4: Database Models and Migrations - Structure Validation")
    print("=" * 60)

    # Check file existence
    print("\n1. Checking file existence:")
    files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/resume.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/unit/__init__.py",
        "tests/unit/test_models.py",
        "tests/integration/__init__.py",
        "tests/integration/test_database.py",
        "pytest.ini",
    ]

    for f in files:
        if not validate_file_exists(base_path / f):
            all_passed = False

    # Check Python syntax
    print("\n2. Checking Python syntax:")
    py_files = [f for f in files if f.endswith('.py')]
    for f in py_files:
        if not validate_python_syntax(base_path / f):
            all_passed = False

    # Check for required classes
    print("\n3. Checking for required classes:")
    class_checks = [
        ("app/core/config.py", "Settings"),
        ("app/core/database.py", "Base"),
        ("app/core/database.py", "DatabaseManager"),
        ("app/models/resume.py", "Resume"),
        ("app/models/resume.py", "ProcessingStatus"),
    ]
    for filepath, class_name in class_checks:
        if not validate_class_exists(base_path / filepath, class_name):
            all_passed = False

    # Check for required functions
    print("\n4. Checking for required functions:")
    function_checks = [
        ("app/core/config.py", "get_settings"),
        ("app/core/database.py", "get_db"),
        ("app/core/database.py", "init_db"),
        ("app/core/database.py", "close_db"),
    ]
    for filepath, func_name in function_checks:
        if not validate_function_exists(base_path / filepath, func_name):
            all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: All structure validation checks PASSED")
        print("=" * 60)
        print("\nNOTE: To run actual tests, install dependencies first:")
        print("  cd /Users/nileshkumar/gh/resume-parser/backend")
        print("  pip install -r requirements.txt")
        print("  pytest tests/ -v")
        return 0
    else:
        print("RESULT: Some structure validation checks FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
