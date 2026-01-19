"""
Helper constants and utilities for world-first structure tests.
Provides expected paths, validation functions, and test utilities.
"""

from pathlib import Path

# Expected world-first structure constants
WORLD_DIR = "00_world"
FOUNDATION_DIRNAME = "00_foundation"
SPEC_DIRNAME = "01_spec"
FORMALISM_DIR = "01_formalism"
PROCESS_REGIME_DIR = "02_process_regime"
FUNCTION_APPLICATION_DIR = "03_function_application"
PAPERS_DIRNAME = "papers"

# Canonical paths
FOUNDATION_REL = Path(WORLD_DIR) / FOUNDATION_DIRNAME
SPEC_REL = Path(WORLD_DIR) / SPEC_DIRNAME

# Expected top-level structure after init
EXPECTED_TOP_LEVEL_DIRS = [
    WORLD_DIR,
    FORMALISM_DIR,
    PROCESS_REGIME_DIR,
    FUNCTION_APPLICATION_DIR,
    "shared",
    "scripts",
    "98_context",
    "99_legacy",
    "releases"
]

# Expected files after init
EXPECTED_INIT_FILES = [
    ".paperrepo",
    ".gitignore",
    # Note: .texrepo-config is created by 'tex-repo config' command, not init
    # World layer
    f"{WORLD_DIR}/README.md",
    f"{FOUNDATION_REL}/README.md",
    f"{FOUNDATION_REL}/{FOUNDATION_DIRNAME}.tex",
    f"{FOUNDATION_REL}/refs.bib",
    f"{FOUNDATION_REL}/sections/00_definitions.tex",
    f"{FOUNDATION_REL}/sections/01_axioms.tex",
    f"{SPEC_REL}/README.md",
    f"{SPEC_REL}/{SPEC_DIRNAME}.tex",
    f"{SPEC_REL}/refs.bib",
    # Layer READMEs
    f"{FORMALISM_DIR}/README.md",
    f"{PROCESS_REGIME_DIR}/README.md",
    f"{FUNCTION_APPLICATION_DIR}/README.md",
    # Papers directories
    f"{FORMALISM_DIR}/{PAPERS_DIRNAME}/.keep",
    f"{PROCESS_REGIME_DIR}/process/{PAPERS_DIRNAME}/.keep",
    f"{PROCESS_REGIME_DIR}/regime/{PAPERS_DIRNAME}/.keep",
    f"{FUNCTION_APPLICATION_DIR}/function/{PAPERS_DIRNAME}/.keep",
    f"{FUNCTION_APPLICATION_DIR}/application/{PAPERS_DIRNAME}/.keep",
    # Shared files
    "shared/identity.tex",
    "shared/preamble.tex",
    "shared/notation.tex",
]

# Expected build directories that should be created
EXPECTED_BUILD_DIRS = [
    f"{FOUNDATION_REL}/build",
    f"{SPEC_REL}/build",
]

def check_world_first_structure(repo_path: Path) -> tuple[bool, list[str]]:
    """
    Check if a repository has the correct world-first structure.
    Returns (is_valid, errors).
    """
    errors = []
    
    # Check top-level directories
    for dir_name in [WORLD_DIR, FORMALISM_DIR, PROCESS_REGIME_DIR, FUNCTION_APPLICATION_DIR]:
        if not (repo_path / dir_name).is_dir():
            errors.append(f"Missing top-level directory: {dir_name}")
    
    # Check world layer
    foundation_dir = repo_path / FOUNDATION_REL
    spec_dir = repo_path / SPEC_REL
    
    if not foundation_dir.is_dir():
        errors.append(f"Missing foundation directory: {FOUNDATION_REL}")
    else:
        # Check foundation structure
        foundation_tex = foundation_dir / f"{FOUNDATION_DIRNAME}.tex"
        if not foundation_tex.exists():
            errors.append(f"Missing foundation entry file: {foundation_tex}")
        
        for section in ["00_definitions.tex", "01_axioms.tex"]:
            section_path = foundation_dir / "sections" / section
            if not section_path.exists():
                errors.append(f"Missing foundation section: {section_path}")
    
    if not spec_dir.is_dir():
        errors.append(f"Missing spec directory: {SPEC_REL}")
    else:
        # Check spec structure
        spec_tex = spec_dir / f"{SPEC_DIRNAME}.tex"
        if not spec_tex.exists():
            errors.append(f"Missing spec entry file: {spec_tex}")
        
        if not (spec_dir / "refs.bib").exists():
            errors.append(f"Missing spec refs.bib")
    
    # Check papers directories
    papers_dirs = [
        f"{FORMALISM_DIR}/{PAPERS_DIRNAME}",
        f"{PROCESS_REGIME_DIR}/process/{PAPERS_DIRNAME}",
        f"{PROCESS_REGIME_DIR}/regime/{PAPERS_DIRNAME}", 
        f"{FUNCTION_APPLICATION_DIR}/function/{PAPERS_DIRNAME}",
        f"{FUNCTION_APPLICATION_DIR}/application/{PAPERS_DIRNAME}"
    ]
    
    for papers_dir in papers_dirs:
        if not (repo_path / papers_dir).is_dir():
            errors.append(f"Missing papers directory: {papers_dir}")
    
    return len(errors) == 0, errors


def check_entry_file_naming(paper_dir: Path) -> tuple[bool, str]:
    """
    Check if a paper directory follows the entry file naming rule.
    Returns (is_valid, message).
    """
    expected_name = f"{paper_dir.name}.tex"
    expected_path = paper_dir / expected_name
    main_tex_path = paper_dir / "main.tex"
    
    if expected_path.exists():
        return True, f"✅ Correct entry file: {expected_name}"
    elif main_tex_path.exists():
        return False, f"❌ Legacy main.tex found, expected: {expected_name}"
    else:
        return False, f"❌ No entry file found, expected: {expected_name}"


def check_required_readmes(repo_path: Path) -> tuple[bool, list[str]]:
    """
    Check if all required READMEs exist.
    Returns (all_exist, missing_list).
    """
    required_readmes = [
        f"{WORLD_DIR}/README.md",
        f"{FOUNDATION_REL}/README.md", 
        f"{SPEC_REL}/README.md",
        f"{FORMALISM_DIR}/README.md",
        f"{PROCESS_REGIME_DIR}/README.md",
        f"{FUNCTION_APPLICATION_DIR}/README.md"
    ]
    
    missing = []
    for readme in required_readmes:
        if not (repo_path / readme).exists():
            missing.append(readme)
    
    return len(missing) == 0, missing


def get_world_terminology() -> list[str]:
    """Return words that should appear in world-first status output."""
    return ["world", "layer", "foundation", "spec"]


def get_legacy_terminology() -> list[str]:
    """Return words that should NOT appear in world-first status output."""
    return ["SPEC", "stage"]