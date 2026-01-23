from __future__ import annotations

from .common import find_repo_root
from .config import create_default_config


def cmd_config(args) -> int:
    """Create a default configuration file."""
    try:
        repo_root = find_repo_root()
        create_default_config(repo_root)
        print("✅ Created default configuration file: .texrepo-config")
        print("Edit this file to customize paper generation and build behavior.")
        return 0
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return 1