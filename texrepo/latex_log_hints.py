from __future__ import annotations

import re
from typing import Dict, List, Optional


def extract_primary_error(log_text: str) -> Dict[str, Optional[str]]:
    """Extract the first fatal-looking LaTeX error block with structured fields."""
    lines = log_text.splitlines()
    text = log_text

    # Pattern A: Runaway argument / fileswith@ptions
    runaway_idx = _find_first_index(lines, r"Runaway argument\?")
    fileswith_idx = _find_first_index(lines, r"\\@fileswith@ptions|fileswith@ptions")
    if runaway_idx is not None or fileswith_idx is not None:
        idx = runaway_idx if runaway_idx is not None else fileswith_idx
        line_no = _extract_line_number_near(lines, idx)
        context = _collect_context(lines, idx)
        return {
            "kind": "runaway",
            "message": "Runaway argument or package options parsing error",
            "line": line_no,
            "context": context,
            "file": _extract_file_near(lines, idx),
            "missing_pkg": None,
            "undefined_cmd": None,
        }

    # Pattern B: Missing .sty (multiple quote variants)
    missing_pkg = _match_missing_package(text)
    if missing_pkg:
        idx = _find_first_index(lines, r"\.sty' not found|\.sty\" not found|\.sty not found")
        return {
            "kind": "missing_pkg",
            "message": f"Package `{missing_pkg}.sty` not found",
            "line": _extract_line_number_near(lines, idx),
            "context": _collect_context(lines, idx),
            "file": _extract_file_near(lines, idx),
            "missing_pkg": missing_pkg,
            "undefined_cmd": None,
        }

    # Pattern C: Undefined control sequence
    undef_idx = _find_first_index(lines, r"! Undefined control sequence\.")
    if undef_idx is not None:
        cmd_line = lines[undef_idx + 1] if undef_idx + 1 < len(lines) else ""
        cmd_match = re.search(r"(\\[A-Za-z@]+\\*?)", cmd_line)
        cmd = cmd_match.group(1) if cmd_match else None
        return {
            "kind": "undefined_cmd",
            "message": f"Undefined control sequence{f' {cmd}' if cmd else ''}".strip(),
            "line": _extract_line_number_near(lines, undef_idx),
            "context": _collect_context(lines, undef_idx),
            "file": _extract_file_near(lines, undef_idx),
            "missing_pkg": None,
            "undefined_cmd": cmd,
        }

    # Pattern D: Unicode character not set up
    uni_idx = _find_first_index(lines, r"inputenc Error: Unicode character|Unicode character .* not set up")
    if uni_idx is not None:
        return {
            "kind": "unicode",
            "message": "Unicode character not configured in LaTeX run",
            "line": _extract_line_number_near(lines, uni_idx),
            "context": _collect_context(lines, uni_idx),
            "file": _extract_file_near(lines, uni_idx),
            "missing_pkg": None,
            "undefined_cmd": None,
        }

    # Fallback: first line starting with "!" error
    bang_idx = _find_first_index(lines, r"^!")
    if bang_idx is not None:
        return {
            "kind": "bang",
            "message": lines[bang_idx].lstrip("! ").strip(),
            "line": _extract_line_number_near(lines, bang_idx),
            "context": _collect_context(lines, bang_idx),
            "file": _extract_file_near(lines, bang_idx),
            "missing_pkg": None,
            "undefined_cmd": None,
        }

    return {
        "kind": "none",
        "message": None,
        "line": None,
        "context": None,
        "file": None,
        "missing_pkg": None,
        "undefined_cmd": None,
    }


def suggest_fixes(error: Dict[str, Optional[str]]) -> List[str]:
    """Return heuristic suggestions based on parsed error."""
    kind = (error.get("kind") or "").lower()
    context = (error.get("context") or "").lower()
    missing_pkg = (error.get("missing_pkg") or "").lower()
    undefined_cmd = error.get("undefined_cmd")
    suggestions: List[str] = []

    if kind == "runaway":
        suggestions.append(
            "Check unmatched [] or {} in \\usepackage[...] lines; syntax example: \\usepackage[nameinlink,noabbrev]{cleveref}"
        )

    if kind == "missing_pkg" and missing_pkg:
        suggestions.extend(_package_install_suggestions(missing_pkg))

    if kind == "undefined_cmd":
        suggestions.extend(_control_sequence_suggestions(context, undefined_cmd))

    if kind == "unicode":
        suggestions.append("Use xelatex/lualatex or add appropriate input encoding (utf8) support")

    # Ensure uniqueness and concise ordering
    deduped = []
    for s in suggestions:
        if s not in deduped:
            deduped.append(s)
    return deduped


def _find_first_index(lines: List[str], pattern: str) -> Optional[int]:
    rx = re.compile(pattern)
    for i, line in enumerate(lines):
        if rx.search(line):
            return i
    return None


def _extract_line_number_near(lines: List[str], idx: Optional[int]) -> Optional[int]:
    if idx is None:
        return None
    window = lines[max(0, idx - 2): idx + 3]
    for line in window:
        m = re.search(r"l\.(\d+)", line)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None


def _extract_file_near(lines: List[str], idx: Optional[int]) -> Optional[str]:
    if idx is None:
        return None
    window = lines[max(0, idx - 5): idx + 6]
    for line in window:
        m = re.search(r"\(([^()]+\.tex)\)", line)
        if m:
            return m.group(1)
    return None


def _collect_context(lines: List[str], idx: Optional[int]) -> Optional[str]:
    if idx is None:
        return None
    start = max(0, idx - 3)
    end = min(len(lines), idx + 6)
    snippet = "\n".join(lines[start:end]).strip()
    return snippet or None


def _match_missing_package(text: str) -> Optional[str]:
    patterns = [
        r"File [`']?\"?([^`'\"\s]+)\.sty[`']?\"? not found",
        r"File ([^`'\"\s]+)\.sty not found",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def _package_install_suggestions(pkg: str) -> List[str]:
    pkg_lower = pkg.lower()
    mapping = {
        "cleveref": "\\usepackage[nameinlink,noabbrev]{cleveref}",
        "natbib": "\\usepackage[numbers]{natbib}",
        "geometry": "\\usepackage{geometry}",
        "graphicx": "\\usepackage{graphicx}",
    }
    hints = []
    if pkg_lower in mapping:
        hints.append(f"Add {mapping[pkg_lower]} to the preamble")
    else:
        hints.append(f"Install or include package `{pkg_lower}` (missing .sty)")
    return hints


def _control_sequence_suggestions(context: str, cmd: Optional[str]) -> List[str]:
    hints = []
    combined = f"{context} {cmd or ''}"
    if "\\cref" in combined or "\\Cref" in combined:
        hints.append("Load cleveref: \\usepackage[nameinlink,noabbrev]{cleveref}")
    if "\\includegraphics" in combined:
        hints.append("Load graphicx: \\usepackage{graphicx}")
    if "\\mathbb" in combined:
        hints.append("Load amsfonts/amsmath: \\usepackage{amsfonts}")
    return hints
