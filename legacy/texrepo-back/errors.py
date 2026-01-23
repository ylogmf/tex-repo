"""
Error reporting utilities for tex-repo CLI commands
"""
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for tex-repo CLI operations"""
    README_MISSING = "README_MISSING"
    INVALID_PLACEMENT = "INVALID_PLACEMENT"  
    SPEC_IMMUTABLE = "SPEC_IMMUTABLE"
    SPEC_MISSING = "SPEC_MISSING"
    STRUCTURE_MISSING = "STRUCTURE_MISSING"
    UNEXPECTED_ITEM = "UNEXPECTED_ITEM"
    MAIN_TEX_MISSING = "MAIN_TEX_MISSING"
    NOT_IN_REPO = "NOT_IN_REPO"
    INVALID_PARENT = "INVALID_PARENT"


def format_error(code: ErrorCode, message: str, path: str = None) -> str:
    """Format error message with consistent prefix and optional path"""
    if path:
        return f"E[{code.value}] {message}: {path}"
    else:
        return f"E[{code.value}] {message}"


def print_error_and_exit(code: ErrorCode, message: str, path: str = None) -> int:
    """Print formatted error message and return exit code 1"""
    print(format_error(code, message, path))
    return 1