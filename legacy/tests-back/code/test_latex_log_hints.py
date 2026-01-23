import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from texrepo.latex_log_hints import extract_primary_error, suggest_fixes  # noqa: E402


FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "latex_logs"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_runaway_argument_hint():
    log_text = _read("runaway_argument.log")
    err = extract_primary_error(log_text)
    assert err["kind"] == "runaway"
    assert "Runaway argument" in (err["message"] or "")
    assert err["line"] is None or isinstance(err["line"], int)
    fixes = suggest_fixes(err)
    assert any("usepackage" in f.lower() for f in fixes)
    assert any("bracket" in f.lower() or "unmatched" in f.lower() for f in fixes)


def test_missing_cleveref_hint():
    log_text = _read("missing_cleveref.log")
    err = extract_primary_error(log_text)
    assert err["kind"] == "missing_pkg"
    assert err["missing_pkg"] == "cleveref"
    assert "cleveref.sty" in (err["message"] or "")
    fixes = suggest_fixes(err)
    assert any("cleveref" in f.lower() for f in fixes)
    assert any("usepackage" in f.lower() for f in fixes)


def test_undefined_cref_hint():
    log_text = _read("undefined_cref.log")
    err = extract_primary_error(log_text)
    assert err["kind"] == "undefined_cmd"
    assert err["undefined_cmd"] == "\\cref"
    assert "Undefined control sequence" in (err["message"] or "")
    fixes = suggest_fixes(err)
    assert any("cleveref" in f.lower() for f in fixes)


def test_missing_cleveref_singlequote_hint():
    log_text = _read("missing_cleveref_singlequote.log")
    err = extract_primary_error(log_text)
    assert err["kind"] == "missing_pkg"
    assert err["missing_pkg"] == "cleveref"
    fixes = suggest_fixes(err)
    assert any("cleveref" in f.lower() for f in fixes)


def test_fileswith_only_hint():
    log_text = _read("fileswith_only.log")
    err = extract_primary_error(log_text)
    assert err["kind"] == "runaway"
    fixes = suggest_fixes(err)
    assert any("usepackage" in f.lower() for f in fixes)
