"""Unit tests for stage name suggestion feature."""
from __future__ import annotations

import pytest
from texrepo.rules import _suggest_closest_stage, _levenshtein_distance


def test_levenshtein_distance():
    """Test Levenshtein distance calculation."""
    assert _levenshtein_distance("", "") == 0
    assert _levenshtein_distance("a", "") == 1
    assert _levenshtein_distance("", "a") == 1
    assert _levenshtein_distance("abc", "abc") == 0
    assert _levenshtein_distance("abc", "abd") == 1
    assert _levenshtein_distance("abc", "ab") == 1
    assert _levenshtein_distance("abc", "abcd") == 1
    assert _levenshtein_distance("kitten", "sitting") == 3


def test_suggest_closest_stage_exact_typo():
    """Test suggestion for common typos."""
    # Off by one character
    assert "02_function_application" in _suggest_closest_stage("03_function_application", "new")
    assert "01_process_regime" in _suggest_closest_stage("02_process_regime", "new")
    
    # Transposition
    assert "00_introduction" in _suggest_closest_stage("00_introdcution", "new")
    
    # Missing character
    assert "03_hypnosis" in _suggest_closest_stage("03_hypnois", "new")


def test_suggest_closest_stage_no_suggestion_for_very_different():
    """Test that no suggestion is given for very different inputs."""
    # Very different string should not get a suggestion
    result = _suggest_closest_stage("xyz_completely_wrong", "new")
    assert result == ""


def test_suggest_closest_stage_case_insensitive():
    """Test that suggestions are case-insensitive."""
    # Mixed case should still match
    assert "00_introduction" in _suggest_closest_stage("00_INTRODUCTION", "new")
    assert "02_function_application" in _suggest_closest_stage("02_Function_Application", "new")


def test_suggest_closest_stage_small_edits():
    """Test suggestions for small edit distances."""
    # 1 character off
    assert "03_hypnosis" in _suggest_closest_stage("03_hypnosiss", "new")
    
    # 2 characters off
    assert "01_process_regime" in _suggest_closest_stage("01_process_regim", "new")
    
    # 3 characters off (boundary)
    suggestion = _suggest_closest_stage("03_hypno", "new")
    assert "03_hypnosis" in suggestion or suggestion == ""


def test_np_error_includes_suggestion():
    """Test that np command error includes stage suggestion."""
    from pathlib import Path
    from texrepo.rules import resolve_paper_path
    from texrepo.common import TexRepoError
    
    # Try to create paper in non-existent stage (typo)
    # resolve_paper_path only needs the user_rel path and layout_name
    with pytest.raises(TexRepoError) as exc_info:
        resolve_paper_path(Path("03_function_application/test_paper"), "new")
    
    # Should raise error with suggestion
    error_msg = str(exc_info.value)
    assert "INVALID_PARENT" in error_msg
    assert "Did you mean '02_function_application'?" in error_msg
