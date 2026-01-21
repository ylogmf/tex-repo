"""
Unit tests for section title formatting in introduction_index.py
"""
import pytest
from pathlib import Path
from texrepo.introduction_index import format_section_title, generate_introduction_index


class TestFormatSectionTitle:
    """Test the format_section_title helper function with book-style capitalization."""
    
    def test_simple_hyphenated(self):
        """Test simple hyphenated section name."""
        assert format_section_title("section-1") == "Section 1"
    
    def test_multi_word_hyphenated(self):
        """Test multi-word hyphenated section name."""
        assert format_section_title("structural-survival") == "Structural Survival"
    
    def test_underscored(self):
        """Test underscored section name."""
        assert format_section_title("type_consistency") == "Type Consistency"
    
    def test_mixed_separators(self):
        """Test mixed hyphens and underscores."""
        assert format_section_title("mixed_name-style") == "Mixed Name Style"
    
    def test_with_numeric_prefix(self):
        """Test with numeric prefix that should be stripped."""
        assert format_section_title("01_section-1") == "Section 1"
        assert format_section_title("02_structural-survival") == "Structural Survival"
        assert format_section_title("03_type_consistency") == "Type Consistency"
    
    def test_acronyms_preserved(self):
        """Test that all-caps acronyms are preserved."""
        assert format_section_title("np_vs_p") == "NP vs P"  # np→NP (2-letter), vs lowercase (connector)
        assert format_section_title("01_NP_vs_P") == "NP vs P"
        assert format_section_title("HTTP_and_REST") == "HTTP and REST"  # and is connector
        assert format_section_title("io_operations") == "IO Operations"  # io is 2-letter lowercase → IO
    
    def test_book_style_connectors(self):
        """Test book-style capitalization with connector words."""
        assert format_section_title("law_of_motion") == "Law of Motion"  # of is lowercase
        assert format_section_title("cost_and_order") == "Cost and Order"  # and is lowercase
        assert format_section_title("inference_in_np") == "Inference in NP"  # in is lowercase
        assert format_section_title("search_for_truth") == "Search for Truth"  # for is lowercase
        assert format_section_title("path_to_success") == "Path to Success"  # to is lowercase
        assert format_section_title("notes_on_logic") == "Notes on Logic"  # on is lowercase
        assert format_section_title("speed_or_accuracy") == "Speed or Accuracy"  # or is lowercase
    
    def test_connector_as_first_word(self):
        """Test that connector words are capitalized when they're the first word."""
        assert format_section_title("of_mice_and_men") == "Of Mice and Men"  # first word capitalized
        assert format_section_title("in_the_beginning") == "In the Beginning"
        assert format_section_title("on_complexity") == "On Complexity"
    
    def test_single_word(self):
        """Test single word section name."""
        assert format_section_title("introduction") == "Introduction"
        assert format_section_title("01_introduction") == "Introduction"
    
    def test_already_formatted(self):
        """Test input that's already well-formatted (no separators)."""
        assert format_section_title("basics") == "Basics"
    
    def test_numbers_in_name(self):
        """Test section names containing numbers."""
        assert format_section_title("chapter-1") == "Chapter 1"
        assert format_section_title("01_part-2a") == "Part 2a"
    
    def test_empty_string(self):
        """Test empty string input."""
        result = format_section_title("")
        # Should not crash, returns something safe
        assert isinstance(result, str)
    
    def test_edge_case_only_prefix(self):
        """Test edge case where input is only numeric prefix."""
        assert format_section_title("01_") == ""
    
    def test_mixed_case_input(self):
        """Test mixed case input."""
        assert format_section_title("mySection_name") == "Mysection Name"
        assert format_section_title("API_design") == "API Design"  # API is all-caps, preserved
    
    def test_fallback_on_unexpected_input(self):
        """Test that function handles unexpected input gracefully."""
        # The function should not crash on unexpected input
        result = format_section_title("weird!!!input")
        assert isinstance(result, str)


class TestTitleOverrides:
    """Test the title.tex override mechanism for mathematical notation."""
    
    def test_title_override_with_math_notation(self, tmp_path):
        """Test that title.tex override is used when present."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        # Create section with override
        section_dir = sections_dir / "01_np_vs_p"
        section_dir.mkdir()
        
        # Create subsection files
        for i in range(1, 11):
            (section_dir / f"1-{i}.tex").write_text(f"% Content 1-{i}")
        
        # Create title override with math notation
        title_file = section_dir / "title.tex"
        title_file.write_text(r"$\alpha$ vs NP")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use override, not formatted folder name
        assert r"\section{$\alpha$ vs NP}" in content
        assert r"\section{NP vs P}" not in content
        
        # Should still include subsections
        assert r"\input{parts/sections/01_np_vs_p/1-1.tex}" in content
        assert r"\input{parts/sections/01_np_vs_p/1-10.tex}" in content
    
    def test_title_override_fallback_missing_file(self, tmp_path):
        """Test fallback to formatted name when title.tex is missing."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        # Create section WITHOUT override
        section_dir = sections_dir / "01_np_vs_p"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use formatted folder name
        assert r"\section{NP vs P}" in content
    
    def test_title_override_fallback_empty_file(self, tmp_path):
        """Test fallback to formatted name when title.tex is empty."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        # Create section with empty override
        section_dir = sections_dir / "01_law_of_motion"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Create empty title override
        title_file = section_dir / "title.tex"
        title_file.write_text("   \n  ")  # whitespace only
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use formatted folder name
        assert r"\section{Law of Motion}" in content
    
    def test_title_override_with_complex_latex(self, tmp_path):
        """Test title override with complex LaTeX content."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Complex LaTeX in title
        title_file = section_dir / "title.tex"
        title_file.write_text(r"The \textbf{P} vs \textsc{NP} Problem: $\mathcal{O}(n^2)$")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should preserve exact LaTeX content
        assert r"\section{The \textbf{P} vs \textsc{NP} Problem: $\mathcal{O}(n^2)$}" in content
    
    def test_title_override_multiple_sections_mixed(self, tmp_path):
        """Test mix of sections with and without overrides."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        # Section 1: with override
        section1 = sections_dir / "01_alpha"
        section1.mkdir()
        (section1 / "1-1.tex").write_text("% Content")
        (section1 / "title.tex").write_text(r"$\alpha$ Complexity")
        
        # Section 2: without override
        section2 = sections_dir / "02_beta_analysis"
        section2.mkdir()
        (section2 / "2-1.tex").write_text("% Content")
        
        # Section 3: with override
        section3 = sections_dir / "03_gamma"
        section3.mkdir()
        (section3 / "3-1.tex").write_text("% Content")
        (section3 / "title.tex").write_text(r"$\gamma$ Reduction")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Section 1: should use override
        assert r"\section{$\alpha$ Complexity}" in content
        
        # Section 2: should use formatted name
        assert r"\section{Beta Analysis}" in content
        
        # Section 3: should use override
        assert r"\section{$\gamma$ Reduction}" in content


class TestTitleOverrideSafety:
    """Test safety guards for title.tex overrides."""
    
    def test_title_override_rejects_section_command(self, tmp_path, capsys):
        """Test that title.tex containing \\section is rejected with warning."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        section_dir = sections_dir / "01_test_section"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Invalid override with \section
        title_file = section_dir / "title.tex"
        title_file.write_text(r"\section{Bad Title}")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should fall back to formatted name, not use the override
        assert r"\section{Test Section}" in content
        assert r"\section{Bad Title}" not in content
        assert r"\section{\section{Bad Title}}" not in content
        
        # Should have emitted warning to stderr
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "01_test_section" in captured.err
        assert "structural commands" in captured.err
    
    def test_title_override_rejects_subsection_command(self, tmp_path, capsys):
        """Test that title.tex containing \\subsection is rejected."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        title_file = section_dir / "title.tex"
        title_file.write_text(r"Title \subsection{subsec}")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should fall back
        assert r"\section{Test}" in content
        
        # Should have warning
        captured = capsys.readouterr()
        assert "Warning" in captured.err
    
    def test_title_override_rejects_input_command(self, tmp_path, capsys):
        """Test that title.tex containing \\input is rejected."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        title_file = section_dir / "title.tex"
        title_file.write_text(r"Title \input{malicious.tex}")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should fall back
        assert r"\section{Test}" in content
        assert r"\input{malicious.tex}" not in content
        
        # Should have warning
        captured = capsys.readouterr()
        assert "Warning" in captured.err
    
    def test_title_override_allows_safe_latex(self, tmp_path, capsys):
        """Test that safe LaTeX commands are still allowed."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Safe LaTeX with formatting and math
        title_file = section_dir / "title.tex"
        title_file.write_text(r"The \textbf{NP} vs \textit{P} Problem: $\alpha^2$")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use the override
        assert r"\section{The \textbf{NP} vs \textit{P} Problem: $\alpha^2$}" in content
        
        # Should NOT have warning
        captured = capsys.readouterr()
        assert "Warning" not in captured.err
