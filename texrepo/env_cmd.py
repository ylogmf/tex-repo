"""Environment support commands for tex-repo.

Provides commands to check system environment and generate setup guides.
Conservative approach - never modifies system without explicit user consent.
"""

import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional


def check_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a tool is available in PATH.
    
    Returns:
        Tuple of (is_available, path_or_none)
    """
    path = shutil.which(tool_name)
    return (path is not None, path)


def check_environment() -> int:
    """Check system environment for tex-repo readiness.
    
    Returns:
        0 if latexmk found, non-zero otherwise
    """
    print("Environment check:")
    
    # OS information
    os_name = platform.system()
    os_version = platform.release()
    print(f"  OS: {os_name} {os_version}")
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  Python: {python_version}")
    print()
    
    # Check required and optional tools
    tools_to_check = {
        'latexmk': 'required',
        'pdflatex': 'optional / compatibility'
    }
    
    missing_required = []
    
    for tool, status in tools_to_check.items():
        is_available, path = check_tool_availability(tool)
        
        if is_available:
            print(f"  {tool}: ✅ found at {path}")
        else:
            print(f"  {tool}: ❌ not found")
            if status == 'required':
                missing_required.append(tool)
    
    print()
    
    # Report on required tools
    if missing_required:
        print("Required:")
        for tool in missing_required:
            if tool == 'latexmk':
                print("  - latexmk is required to build papers.")
        print()
        
        print("Suggested next steps:")
        if os_name == 'Linux':
            print("  Ubuntu/Debian:")
            print("    sudo apt install texlive-full")
            print("  Fedora/RHEL:")
            print("    sudo dnf install texlive-scheme-full")
        elif os_name == 'Darwin':  # macOS
            print("  macOS:")
            print("    brew install --cask mactex")
            print("    # OR download from: https://tug.org/mactex/")
        else:
            print(f"  {os_name}:")
            print("    Install TeX Live from: https://tug.org/texlive/")
        
        return 1
    else:
        print("✅ All required tools are available!")
        return 0


def generate_guide() -> None:
    """Generate env_guide.txt with system-specific setup instructions."""
    os_name = platform.system()
    os_version = platform.release()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check current tool availability
    latexmk_available, latexmk_path = check_tool_availability('latexmk')
    pdflatex_available, pdflatex_path = check_tool_availability('pdflatex')
    
    guide_content = f"""# tex-repo Environment Setup Guide
# Generated automatically by tex-repo env guide
# This file can be safely regenerated - do not edit manually

## System Information

Detected OS: {os_name} {os_version}
Python Version: {python_version}
Generated on: $(date +"%Y-%m-%d %H:%M:%S")

## Current Tool Status

latexmk: {'✅ found at ' + latexmk_path if latexmk_available else '❌ not found'}
pdflatex: {'✅ found at ' + pdflatex_path if pdflatex_available else '❌ not found'}

## Required Tools

### latexmk (Required)
tex-repo standardizes on latexmk for reliable multi-pass LaTeX compilation.
latexmk automatically handles:
- Multiple compilation passes for references and citations
- Bibliography processing (bibtex/biber)
- Index generation if needed
- Dependency tracking and incremental builds

### pdflatex (Optional)
pdflatex support is maintained for legacy compatibility only.
tex-repo automatically runs pdflatex twice when needed for references.

## Installation Instructions

"""
    
    if os_name == 'Linux':
        guide_content += """### Ubuntu/Debian Systems
```bash
# Full TeX Live installation (recommended)
sudo apt update
sudo apt install texlive-full

# Minimal installation (if disk space is limited)
sudo apt install texlive-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended
```

### Fedora/RHEL/CentOS Systems
```bash
# Full TeX Live installation (recommended)
sudo dnf install texlive-scheme-full

# Minimal installation
sudo dnf install texlive-base texlive-latex texlive-collection-latexrecommended
```

### Other Linux Distributions
Install TeX Live from the official distribution: https://tug.org/texlive/

"""
    elif os_name == 'Darwin':  # macOS
        guide_content += """### macOS Systems

#### Option 1: MacTeX (Full Distribution - Recommended)
```bash
# Using Homebrew
brew install --cask mactex

# OR download directly from https://tug.org/mactex/
# MacTeX includes everything needed and is well-maintained
```

#### Option 2: BasicTeX (Minimal Installation)
```bash
# Using Homebrew (smaller download, may need additional packages)
brew install --cask basictex

# You may need to install additional packages later:
sudo tlmgr update --self
sudo tlmgr install collection-latexrecommended collection-fontsrecommended
```

"""
    else:
        guide_content += f"""### {os_name} Systems
Please install TeX Live from the official distribution:
https://tug.org/texlive/

Ensure that the installation includes latexmk and places it in your system PATH.

"""
    
    guide_content += """## Verification

After installation, verify your setup with:
```bash
tex-repo env check
```

This should show ✅ for latexmk if installation was successful.

## Notes

- tex-repo requires only latexmk to function properly
- pdflatex is optional and used only for compatibility
- A full TeX Live installation provides the most reliable experience
- Partial installations may work but could require manual package installation later
- tex-repo will detect and report missing tools before building papers

## Troubleshooting

If latexmk is not found after installation:
1. Check that your TeX distribution is in PATH: `echo $PATH`
2. Restart your terminal/shell session
3. On macOS with MacTeX: ensure /usr/local/texlive/*/bin/*/latexmk exists
4. On Linux: ensure texlive-binaries or equivalent package is installed

For more help, see tex-repo documentation or file an issue.
"""
    
    # Write guide to file
    guide_path = Path('env_guide.txt')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"Environment setup guide written to: {guide_path.absolute()}")
    print()
    print("To execute installation commands from this guide:")
    print(f"  tex-repo install {guide_path}")
    print()
    print("Note: The install command requires explicit confirmation")
    print("      and is intended for personal use only.")