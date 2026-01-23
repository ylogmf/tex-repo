"""Core utilities for tex-repo."""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple


# Connector words for title capitalization
CONNECTORS = {"vs", "and", "or", "of", "in", "on", "for", "to", "the", "a", "an"}


def slug_to_title(slug: str) -> str:
    """
    Convert a directory slug to a display title.
    
    Rules:
    - First word is always capitalized
    - Connector words are lowercased unless first
    - All-uppercase tokens are preserved
    - Numeric tokens are preserved
    - Underscores and hyphens are word separators
    
    Examples:
        np_vs_p -> NP vs P
        law_of_motion -> Law of Motion
        in_the_beginning -> In the Beginning
        section_1 -> Section 1
    """
    # Split on underscores and hyphens
    words = re.split(r'[_-]', slug)
    
    result = []
    for i, word in enumerate(words):
        if not word:
            continue
            
        # First word: always capitalize first letter
        if i == 0:
            if word.isupper() and len(word) > 1:
                result.append(word)  # Preserve acronyms like NP
            else:
                result.append(word.capitalize())
        # Connector words: lowercase unless it's all uppercase
        elif word.lower() in CONNECTORS:
            if word.isupper() and len(word) > 1:
                result.append(word)  # Preserve acronyms
            else:
                result.append(word.lower())
        # All uppercase: preserve
        elif word.isupper() and len(word) > 1:
            result.append(word)
        # Numeric: preserve
        elif word.isdigit():
            result.append(word)
        # Short tokens (1-2 chars): treat as acronyms if not connector
        elif len(word) <= 2 and word.lower() not in CONNECTORS:
            result.append(word.upper())
        # Default: capitalize
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def find_repo_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the repository root by looking for .paperrepo marker.
    
    Args:
        start_path: Starting directory (default: current working directory)
        
    Returns:
        Path to repository root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    while current != current.parent:
        if (current / '.paperrepo').exists():
            return current
        current = current.parent
    
    # Check root directory
    if (current / '.paperrepo').exists():
        return current
    
    return None


def find_book_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the book root (00_introduction/) by traversing upward.
    
    Args:
        start_path: Starting directory (default: current working directory)
        
    Returns:
        Path to book root, or None if not in a book
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    while current != current.parent:
        if current.name == '00_introduction':
            return current
        # Check if current has parts/ directory (book marker)
        if (current / 'parts' / 'parts').exists():
            return current
        current = current.parent
    
    return None


def find_part_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the part root directory by looking for part.tex or chapters/ directory.
    
    Args:
        start_path: Starting directory (default: current working directory)
        
    Returns:
        Path to part root, or None if not in a part
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    while current != current.parent:
        # Check if this is a part directory
        if (current / 'part.tex').exists() and (current / 'chapters').exists():
            return current
        # Check if we're inside a chapters/ directory
        if current.name == 'chapters' and (current.parent / 'part.tex').exists():
            return current.parent
        current = current.parent
    
    return None


def find_next_number(parent_dir: Path, pattern: str = r'^(\d\d)_') -> str:
    """
    Find the next available NN_ prefix in a directory.
    
    Args:
        parent_dir: Directory to scan
        pattern: Regex pattern to match (default: NN_ prefix)
        
    Returns:
        Next available number as a zero-padded string (e.g., "00", "01")
    """
    if not parent_dir.exists():
        return "00"
    
    max_num = -1
    for child in parent_dir.iterdir():
        match = re.match(pattern, child.name)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)
    
    return f"{max_num + 1:02d}"


def validate_slug(slug: str) -> bool:
    """
    Validate that a slug follows naming rules.
    
    Rules:
    - Lowercase only
    - Words separated by underscores or hyphens
    - No spaces, no special characters besides _ and -
    - Must not start or end with separator
    - No placeholder names (e.g., "placeholder", "todo", "temp")
    
    Returns:
        True if valid, False otherwise
    """
    # Check for invalid characters
    if not re.match(r'^[a-z0-9_-]+$', slug):
        return False
    
    # Must not start or end with separator
    if slug.startswith(('_', '-')) or slug.endswith(('_', '-')):
        return False
    
    # No double separators
    if '__' in slug or '--' in slug or '_-' in slug or '-_' in slug:
        return False
    
    # No placeholder names
    placeholder_names = {'placeholder', 'todo', 'temp', 'test', 'tmp', 'tbd'}
    if slug in placeholder_names:
        return False
    
    return True


def make_slug(title: str) -> str:
    """
    Convert a title to a valid slug.
    
    Args:
        title: Human-readable title
        
    Returns:
        Valid slug (lowercase, underscores for spaces)
    """
    # Convert to lowercase
    slug = title.lower()
    
    # Replace spaces and multiple separators with single underscore
    slug = re.sub(r'[\s_-]+', '_', slug)
    
    # Remove invalid characters
    slug = re.sub(r'[^a-z0-9_-]', '', slug)
    
    # Remove leading/trailing separators
    slug = slug.strip('_-')
    
    return slug


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed."""
    ensure_dir(path.parent)
    path.write_text(content)


def read_file_safe(path: Path) -> Optional[str]:
    """Read file content, return None if file doesn't exist."""
    try:
        return path.read_text()
    except FileNotFoundError:
        return None


def get_numbered_dirs(parent: Path, pattern: str = r'^(\d\d)_(.+)$') -> List[Tuple[int, str, Path]]:
    """
    Get all numbered directories in a parent directory.
    
    Args:
        parent: Directory to scan
        pattern: Regex pattern (default: NN_slug)
        
    Returns:
        List of (number, slug, path) tuples, sorted by number
    """
    if not parent.exists():
        return []
    
    results = []
    for child in parent.iterdir():
        if not child.is_dir():
            continue
        match = re.match(pattern, child.name)
        if match:
            num = int(match.group(1))
            slug = match.group(2)
            results.append((num, slug, child))
    
    return sorted(results, key=lambda x: x[0])
