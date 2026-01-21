"""
Tests for introduction index generation.
"""
import tempfile
from pathlib import Path
import pytest

from texrepo.introduction_index import generate_introduction_index, generate_chapters_index


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
        
        # Check section header (now formatted as title case)
        assert r"\section{Framing}" in content
        
        # Check subsection includes
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
        
        # Check sections appear in order (now formatted as title case)
        first_pos = content.find(r"\section{First}")
        second_pos = content.find(r"\section{Second}")
        third_pos = content.find(r"\section{Third}")
        
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
        # Now formats to title case with spaces
        assert r"\section{Hello World Test}" in content
    
    def test_empty_section_folder(self, tmp_path):
        """Test that empty section folders are skipped."""
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
        
        # Extract section input lines (skip frontmatter/backmatter)
        lines = [line for line in content.split('\n') if r'\input{' in line and 'sections/' in line]
        
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

    def test_chapters_index_generation(self, tmp_path):
        """Test that chapters_index.tex is generated with chapter includes in order."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()

        for n, name in [(2, "second"), (1, "first")]:
            section_dir = sections_dir / f"0{n}_{name}"
            section_dir.mkdir()
            (section_dir / "chapter.tex").write_text("% chapter", encoding="utf-8")

        output = generate_chapters_index(intro_dir)
        content = output.read_text()

        first_pos = content.find("sections/01_first/chapter.tex")
        second_pos = content.find("sections/02_second/chapter.tex")
        assert first_pos < second_pos
        assert content.startswith("% Auto-generated chapter include list")

    def test_chapters_index_skips_missing_chapter(self, tmp_path):
        """Chapters index should skip sections without chapter.tex."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()

        good = sections_dir / "01_good"
        good.mkdir()
        (good / "chapter.tex").write_text("% ok", encoding="utf-8")

        missing = sections_dir / "02_missing"
        missing.mkdir()

        output = generate_chapters_index(intro_dir)
        content = output.read_text()

        assert "sections/01_good/chapter.tex" in content
        assert "02_missing" not in content


class TestAppendixSupport:
    """Test appendix support in index generation."""
    
    def test_no_appendix_directory(self, tmp_path):
        """Test that no appendix code is generated when appendix/ doesn't exist."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        
        # Create a section
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should not contain \appendix
        assert "\\appendix" not in content
    
    def test_empty_appendix_directory(self, tmp_path):
        """Test that no appendix code is generated when appendix/ is empty."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        (intro_dir / "appendix").mkdir()
        
        # Create a section
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should not contain \appendix
        assert "\\appendix" not in content
    
    def test_appendix_with_files(self, tmp_path):
        """Test that appendix files are included after sections."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        appendix_dir = intro_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create a section
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Create appendix files
        (appendix_dir / "01_notation.tex").write_text("% Notation")
        (appendix_dir / "02_proofs.tex").write_text("% Proofs")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should contain \appendix
        assert "\\appendix" in content
        
        # Should contain appendix includes
        assert "\\input{appendix/01_notation.tex}" in content
        assert "\\input{appendix/02_proofs.tex}" in content
        
        # Appendix should come after sections
        section_pos = content.find("\\input{sections/01_test/1-1.tex}")
        appendix_pos = content.find("\\appendix")
        assert section_pos < appendix_pos
    
    def test_appendix_files_sorted(self, tmp_path):
        """Test that appendix files are included in sorted order."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        (intro_dir / "sections").mkdir()
        appendix_dir = intro_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create appendix files out of order
        (appendix_dir / "03_third.tex").write_text("% Third")
        (appendix_dir / "01_first.tex").write_text("% First")
        (appendix_dir / "02_second.tex").write_text("% Second")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Check order
        first_pos = content.find("appendix/01_first.tex")
        second_pos = content.find("appendix/02_second.tex")
        third_pos = content.find("appendix/03_third.tex")
        
        assert first_pos < second_pos < third_pos
    
    def test_appendix_ignores_non_tex_files(self, tmp_path):
        """Test that only .tex files in appendix/ are included."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        (intro_dir / "sections").mkdir()
        appendix_dir = intro_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create various files
        (appendix_dir / "01_include.tex").write_text("% Include")
        (appendix_dir / "readme.md").write_text("# README")
        (appendix_dir / "data.txt").write_text("data")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should only include .tex file
        assert "appendix/01_include.tex" in content
        assert "readme.md" not in content
        assert "data.txt" not in content
    
    def test_chapters_index_with_appendix(self, tmp_path):
        """Test that chapters_index.tex includes appendix after chapters."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        appendix_dir = intro_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create a section with chapter
        section_dir = sections_dir / "01_chapter"
        section_dir.mkdir()
        (section_dir / "chapter.tex").write_text("% Chapter")
        
        # Create appendix files
        (appendix_dir / "01_appendix.tex").write_text("% Appendix")
        
        output = generate_chapters_index(intro_dir)
        content = output.read_text()
        
        # Should contain both chapter and appendix
        assert "sections/01_chapter/chapter.tex" in content
        assert "\\appendix" in content
        assert "appendix/01_appendix.tex" in content
        
        # Appendix should come after chapter
        chapter_pos = content.find("sections/01_chapter/chapter.tex")
        appendix_pos = content.find("\\appendix")
        assert chapter_pos < appendix_pos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
