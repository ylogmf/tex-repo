from __future__ import annotations

import os
from pathlib import Path
from configparser import ConfigParser

from .common import find_repo_root, write_text


def parse_paperrepo_metadata(repo_root: Path) -> dict[str, str]:
    """Parse metadata from .paperrepo file."""
    paperrepo_file = repo_root / ".paperrepo"
    if not paperrepo_file.exists():
        return {}
    
    # Read as simple key=value pairs (not using ConfigParser sections)
    metadata = {}
    try:
        with open(paperrepo_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    metadata[key.strip()] = value.strip()
    except Exception:
        # If parsing fails, return empty dict
        pass
    
    return metadata


def write_paperrepo_metadata(repo_root: Path, metadata: dict[str, str]) -> None:
    """Write metadata to .paperrepo file, preserving existing format."""
    paperrepo_file = repo_root / ".paperrepo"
    
    # Read existing content
    existing_lines = []
    if paperrepo_file.exists():
        with open(paperrepo_file, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()
    
    # Prepare output lines - start with existing non-metadata lines
    output_lines = []
    metadata_keys = set()
    
    # Process existing lines, updating metadata keys we find
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key, _ = stripped.split('=', 1)
            key = key.strip()
            if key in metadata:
                # Update this metadata key
                output_lines.append(f"{key}={metadata[key]}\n")
                metadata_keys.add(key)
            else:
                # Keep existing non-metadata key as-is
                output_lines.append(line)
        else:
            # Keep comments and empty lines
            output_lines.append(line)
    
    # Add any new metadata keys that weren't in the file
    for key, value in metadata.items():
        if key not in metadata_keys:
            output_lines.append(f"{key}={value}\n")
    
    # Write back to file
    with open(paperrepo_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)


def escape_latex_string(s: str) -> str:
    """Escape LaTeX special characters minimally."""
    # Only escape the most problematic characters
    replacements = {
        '%': r'\%',
        '&': r'\&',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
    }
    
    result = s
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    
    return result


def generate_identity_tex(metadata: dict[str, str]) -> str:
    """Generate identity.tex content from metadata."""
    
    # Helper function to get value or default
    def get_value(key: str, default: str = "") -> str:
        return escape_latex_string(metadata.get(key, default))
    
    # Generate the LaTeX content
    content = [
        "% Auto-generated. Do not edit by hand.",
        "",
        "% Repository metadata macros",
        f"\\newcommand{{\\RepoProjectName}}{{{get_value('project_name')}}}",
        f"\\newcommand{{\\RepoAuthorName}}{{{get_value('author_name')}}}",
        f"\\newcommand{{\\RepoAuthorEmail}}{{{get_value('author_email')}}}",
        f"\\newcommand{{\\RepoOrganization}}{{{get_value('organization')}}}",
        f"\\newcommand{{\\RepoAuthorAffil}}{{{get_value('default_author_affil', metadata.get('organization', ''))}}}",
        f"\\newcommand{{\\RepoShortAffil}}{{{get_value('short_affiliation', metadata.get('organization', ''))}}}",
        f"\\newcommand{{\\RepoORCID}}{{{get_value('author_orcid')}}}",
        f"\\newcommand{{\\RepoLicense}}{{{get_value('license')}}}",
        f"\\newcommand{{\\RepoDatePolicy}}{{{get_value('date_policy')}}}",
        f"\\newcommand{{\\RepoBibStyle}}{{{get_value('default_bibliography_style')}}}",
        ""
    ]
    
    return "\n".join(content)


def sync_identity_tex(repo_root: Path) -> None:
    """Regenerate shared/identity.tex from .paperrepo metadata."""
    metadata = parse_paperrepo_metadata(repo_root)
    identity_content = generate_identity_tex(metadata)
    
    identity_path = repo_root / "shared" / "identity.tex"
    write_text(identity_path, identity_content)


def prompt_for_metadata(repo_name: str) -> dict[str, str]:
    """Interactively prompt user for repository metadata."""
    metadata = {}
    
    print("\n📝 Repository metadata setup:")
    print("   Press Enter to use defaults shown in [brackets]")
    print("")
    
    # Prompt for each field in order
    prompts = [
        ("project_name", f"Project name [{repo_name}]: ", repo_name),
        ("author_name", "Author name [TODO_AUTHOR]: ", "TODO_AUTHOR"),
        ("organization", "Organization [TODO_ORG]: ", "TODO_ORG"),
        ("author_email", "Author email []: ", ""),
        ("default_author_affil", "Default author affiliation [use organization]: ", ""),  # Special handling
        ("short_affiliation", "Short affiliation []: ", ""),
        ("author_orcid", "Author ORCID []: ", ""),
        ("license", "License [All Rights Reserved]: ", "All Rights Reserved"),
        ("date_policy", "Date policy (today/fixed) [today]: ", "today"),
        ("default_bibliography_style", "Default bibliography style [plainnat]: ", "plainnat"),
    ]
    
    for key, prompt_text, default_value in prompts:
        try:
            response = input(prompt_text).strip()
            if not response:
                if key == "default_author_affil":
                    # Special case: if empty, use organization value
                    metadata[key] = metadata.get("organization", "TODO_ORG")
                else:
                    metadata[key] = default_value
            else:
                metadata[key] = response
        except (KeyboardInterrupt, EOFError):
            # If user interrupts, use defaults for remaining fields
            print("\nUsing defaults for remaining fields...")
            metadata[key] = default_value if key != "default_author_affil" else metadata.get("organization", "TODO_ORG")
            break
    
    # Fill in any missing keys with defaults
    defaults = {
        "project_name": repo_name,
        "author_name": "TODO_AUTHOR",
        "organization": "TODO_ORG",
        "author_email": "",
        "default_author_affil": metadata.get("organization", "TODO_ORG"),
        "short_affiliation": "",
        "author_orcid": "",
        "license": "All Rights Reserved",
        "date_policy": "today",
        "default_bibliography_style": "plainnat",
    }
    
    for key, default in defaults.items():
        if key not in metadata:
            if key == "default_author_affil":
                metadata[key] = metadata.get("organization", "TODO_ORG")
            else:
                metadata[key] = default
    
    print("")
    return metadata


def cmd_sync_meta(args) -> int:
    """Regenerate shared/identity.tex from .paperrepo metadata."""
    try:
        repo_root = find_repo_root()
        sync_identity_tex(repo_root)
        print("✅ Regenerated shared/identity.tex from repository metadata")
        return 0
    except Exception as e:
        print(f"❌ Error syncing metadata: {e}")
        return 1