"""
Tests for introduction index generation.
"""
import tempfile
from pathlib import Path
import pytest

from texrepo.introduction_index import generate_introduction_index


class TestIntroductionIndex:
    """Test the introduction index generator."""
    
    def test_empty_sections_dir(self, tmp_path):
        """Test generation with no sections."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        (intro_dir / "sections").mkdir()
        
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        # With no sections, file should just have the header comments
        assert "Auto-generated" in content
    
    def test_no_sections_dir(self, tmp_path):
        """Test generation when sections/ doesn't exist."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        # With no sections directory, file should still be generated
        assert "Auto-generated" in content
    
    def test_single_section_with_subsections(self, tmp_path):
        """Test generation with one section and subsection files."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        # Create a section folder
        section_dir = sections_dir / "01_framing"
        section_dir.mkdir()
        
        # Create subsection files
        for i in range(1, 11):
            (section_dir / f"1-{i}.tex").write_text(f"% Subsection 1-{i}")
        
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        
        # Check section header
        assert r"\section{framing}" in content
        
        # Check all subsection includes
        for i in range(1, 11):
            assert f"\\input{{sections/01_framing/1-{i}.tex}}" in content
    
    def test_multiple_sections_ordered(self, tmp_path):
        """Test generation with multiple sections in correct order."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        # Create sections out of order
        for section_num, section_name in [(3, "third"), (1, "first"), (2, "second")]:
            section_dir = sections_dir / f"0{section_num}_{section_name}"
            section_dir.mkdir()
            
            # Create a few subsection files
            for i in range(1, 4):
                (section_dir / f"{section_num}-{i}.tex").write_text(f"% Content {section_num}-{i}")
        
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        
        # Check sections appear in order
        first_pos = content.find(r"\section{first}")
        second_pos = content.find(r"\section{second}")
        third_pos = content.find(r"\section{third}")
        
        assert first_pos < second_pos < third_pos
        
        # Check subsections
        assert r"\input{sections/01_first/1-1.tex}" in content
        assert r"\input{sections/02_second/2-1.tex}" in content
        assert r"\input{sections/03_third/3-1.tex}" in content
    
    def test_section_with_underscores_in_name(self, tmp_path):
        """Test that underscores in section names are converted to spaces."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        section_dir = sections_dir / "01_hello_world_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        output = generate_introduction_index(intro_dir)
        
        content = output.read_text()
        assert r"\section{hello world test}" in content
    
    def test_only_includes_matching_section_number(self, tmp_path):
        """Test that only subsections matching the section number are included."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        
        # Create files with correct and incorrect section numbers
        (section_dir / "1-1.tex").write_text("% Correct")
        (section_dir / "1-2.tex").write_text("% Correct")
        (section_dir / "2-1.tex").write_text("% Wrong section number")
        (section_dir / "other.tex").write_text("% Wrong format")
        
        output = generate_introduction_index(intro_dir)
        
        content = output.read_text()
        
        # Only 1-1 and 1-2 should be included
        assert r"\input{sections/01_test/1-1.tex}" in content
        assert r"\input{sections/01_test/1-2.tex}" in content
        assert "2-1.tex" not in content
        assert "other.tex" not in content
    
    def test_subsections_sorted_by_number(self, tmp_path):
        """Test that subsection files are sorted numerically."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        
        # Create files out of order
        for i in [3, 1, 10, 2, 5]:
            (section_dir / f"1-{i}.tex").write_text(f"% Content {i}")
        
        output = generate_introduction_index(intro_dir)
        
        content = output.read_text()
        
        # Extract input lines
        lines = [line for line in content.split('\n') if r'\input{' in line]
        
        # Check order
        assert lines[0].endswith("1-1.tex}")
        assert lines[1].endswith("1-2.tex}")
        assert lines[2].endswith("1-3.tex}")
        assert lines[3].endswith("1-5.tex}")
        assert lines[4].endswith("1-10.tex}")
    
    def test_build_directory_created(self, tmp_path):
        """Test that build directory is created if it doesn't exist."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        (intro_dir / "sections").mkdir()
        
        assert not (intro_dir / "build").exists()
        
        output = generate_introduction_index(intro_dir)
        
        assert output.parent.exists()
        assert output.parent.name == "build"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
