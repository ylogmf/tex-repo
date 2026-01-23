from __future__ import annotations

from pathlib import Path
from configparser import ConfigParser
from typing import Dict, Any

from .common import find_repo_root


DEFAULT_CONFIG = {
    'paper': {
        'section_count': '10',
        'document_class': 'article',
        'document_options': '11pt',
        'include_abstract': 'true',
    },
    'build': {
        'default_engine': 'latexmk',
        'parallel_builds': 'true',
    }
}


def get_config(repo_root: Path = None) -> Dict[str, Any]:
    """Load configuration from .texrepo-config file or use defaults."""
    if repo_root is None:
        try:
            repo_root = find_repo_root()
        except:
            return DEFAULT_CONFIG
    
    config_file = repo_root / ".texrepo-config"
    
    if not config_file.exists():
        return DEFAULT_CONFIG
    
    config = ConfigParser()
    config.read_dict(DEFAULT_CONFIG)  # Start with defaults
    
    try:
        config.read(config_file)
        
        # Convert to regular dict for easier access
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        
        return result
    except Exception:
        # If config file is malformed, use defaults
        return DEFAULT_CONFIG


def get_paper_config(repo_root: Path = None) -> Dict[str, Any]:
    """Get paper-specific configuration."""
    config = get_config(repo_root)
    paper_config = config.get('paper', {})
    
    # Convert string values to appropriate types
    return {
        'section_count': int(paper_config.get('section_count', '10')),
        'document_class': paper_config.get('document_class', 'article'),
        'document_options': paper_config.get('document_options', '11pt'),
        'include_abstract': paper_config.get('include_abstract', 'true').lower() == 'true',
    }


def create_default_config(repo_root: Path) -> None:
    """Create a default .texrepo-config file."""
    config = ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    
    config_file = repo_root / ".texrepo-config"
    with open(config_file, 'w') as f:
        f.write("# tex-repo configuration file\n")
        f.write("# Customize paper generation and build behavior\n\n")
        config.write(f)