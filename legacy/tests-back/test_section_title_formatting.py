"""
Unit tests for section title formatting in introduction_index.py
"""
import pytest
from pathlib import Path
from texrepo.introduction_index import format_title, generate_introduction_index


class TestFormatSectionTitle:
    """Test the format_title helper function with book-style capitalization."""
    
    def test_simple_hyphenated(self):
        """Test simple hyphenated section name."""
        assert format_title("section-1") == "Section 1"
    
    def test_multi_word_hyphenated(self):
        """Test multi-word hyphenated section name."""
        assert format_title("structural-survival") == "Structural Survival"
    
    def test_underscored(self):
        """Test underscored section name."""
        assert format_title("type_consistency") == "Type Consistency"
    
    def test_mixed_separators(self):
        """Test mixed hyphens and underscores."""
        assert format_title("mixed_name-style") == "Mixed Name Style"
    
    def test_with_numeric_prefix(self):
        """Test with numeric prefix that should be stripped."""
        assert format_title("01_section-1") == "Section 1"
        assert format_title("02_structural-survival") == "Structural Survival"
        assert format_title("03_type_consistency") == "Type Consistency"
    
    def test_acronyms_preserved(self):
        """Test that all-caps acronyms are preserved."""
        assert format_title("np_vs_p") == "NP vs P"  # np→NP (2-letter), vs lowercase (connector)
        assert format_title("01_NP_vs_P") == "NP vs P"
        assert format_title("HTTP_and_REST") == "HTTP and REST"  # and is connector
        assert format_title("io_operations") == "IO Operations"  # io is 2-letter lowercase → IO
    
    def test_book_style_connectors(self):
        """Test book-style capitalization with connector words."""
        assert format_title("law_of_motion") == "Law of Motion"  # of is lowercase
        assert format_title("cost_and_order") == "Cost and Order"  # and is lowercase
        assert format_title("inference_in_np") == "Inference in NP"  # in is lowercase
        assert format_title("search_for_truth") == "Search for Truth"  # for is lowercase
        assert format_title("path_to_success") == "Path to Success"  # to is lowercase
        assert format_title("notes_on_logic") == "Notes on Logic"  # on is lowercase
        assert format_title("speed_or_accuracy") == "Speed or Accuracy"  # or is lowercase
    
    def test_connector_as_first_word(self):
        """Test that connector words are capitalized when they're the first word."""
        assert format_title("of_mice_and_men") == "Of Mice and Men"  # first word capitalized
        assert format_title("in_the_beginning") == "In the Beginning"
        assert format_title("on_complexity") == "On Complexity"
    
    def test_single_word(self):
        """Test single word section name."""
        assert format_title("introduction") == "Introduction"
        assert format_title("01_introduction") == "Introduction"
    
    def test_already_formatted(self):
        """Test input that's already well-formatted (no separators)."""
        assert format_title("basics") == "Basics"
    
    def test_numbers_in_name(self):
        """Test section names containing numbers."""
        assert format_title("chapter-1") == "Chapter 1"
        assert format_title("01_part-2a") == "Part 2a"
    
    def test_empty_string(self):
        """Test empty string input."""
        result = format_title("")
        # Should not crash, returns something safe
        assert isinstance(result, str)
    
    def test_edge_case_only_prefix(self):
        """Test edge case where input is only numeric prefix."""
        assert format_title("01_") == ""
    
    def test_mixed_case_input(self):
        """Test mixed case input."""
        assert format_title("mySection_name") == "Mysection Name"
        assert format_title("API_design") == "API Design"  # API is all-caps, preserved
    
    def test_fallback_on_unexpected_input(self):
        """Test that function handles unexpected input gracefully."""
        # The function should not crash on unexpected input
        result = format_title("weird!!!input")
        assert isinstance(result, str)
