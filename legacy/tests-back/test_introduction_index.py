"""
Tests for introduction index generation with Part/Chapter structure.
"""
import tempfile
from pathlib import Path
import pytest

from texrepo.introduction_index import generate_introduction_index, generate_chapters_index


def _make_intro_parts_tree(intro_dir):
    """Create required parts/ tree structure for introduction with Part/Chapter layout."""
    parts_dir = intro_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create frontmatter
    frontmatter_dir = parts_dir / "frontmatter"
    frontmatter_dir.mkdir(exist_ok=True)
    (frontmatter_dir / "title.tex").write_text("% Title\n")
    (frontmatter_dir / "preface.tex").write_text("% Preface\n")
    (frontmatter_dir / "how_to_read.tex").write_text("% How to read\n")
    (frontmatter_dir / "toc.tex").write_text("% TOC\n")
    
    # Create backmatter
    backmatter_dir = parts_dir / "backmatter"
    backmatter_dir.mkdir(exist_ok=True)
    (backmatter_dir / "scope_limits.tex").write_text("% Scope\n")
    (backmatter_dir / "closing_notes.tex").write_text("% Closing\n")
    
    # Create parts directory (NEW: parts/parts/ for book Parts)
    parts_root = parts_dir / "parts"
    parts_root.mkdir(exist_ok=True)
    
    return parts_dir


class TestIntroductionIndexWithPartChapter:
    """Test the introduction index generator with Part/Chapter structure."""
    
    def test_empty_parts_dir(self, tmp_path):
        """Test generation with no parts."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        _make_intro_parts_tree(intro_dir)
        
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        # With no parts, file should have frontmatter and backmatter
        assert "Auto-generated" in content
        assert "frontmatter" in content
        assert "backmatter" in content
    
    def test_single_part_with_chapter(self, tmp_path):
        """Test generation with one part and one chapter."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = _make_intro_parts_tree(intro_dir)
        parts_root = parts_dir / "parts"
        
        # Create a part folder
        part_dir = parts_root / "01_foundations"
        part_dir.mkdir()
        (part_dir / "part.tex").write_text(r"\part{Foundations}" + "\n\n% Part intro\n")
        
        # Create chapters directory
        chapters_dir = part_dir / "chapters"
        chapters_dir.mkdir()
        
        # Create a chapter
        chapter_dir = chapters_dir / "01_basic_concepts"
        chapter_dir.mkdir()
        (chapter_dir / "chapter.tex").write_text(r"\chapter{Basic Concepts}" + "\n\n% Chapter intro\n")
        
        # Create section files
        for i in range(1, 11):
            (chapter_dir / f"1-{i}.tex").write_text(f"\\section{{Section {i}}}\n% Content\n")
        
        # Generate sections_index (FRONTMATTER-ONLY spine)
        output = generate_introduction_index(intro_dir)
        
        assert output.exists()
        content = output.read_text()
        
        # sections_index.tex should be frontmatter-only (no chapter/section content!)
        assert "01_basic_concepts/chapter.tex" not in content
        assert "1-1.tex" not in content
        
        # Generate chapters_index (MAINMATTER spine with all content)
        chapters_output = generate_chapters_index(intro_dir)
        chapters_content = chapters_output.read_text()
        
        # Check that part.tex and chapter.tex are included in chapters_index
        assert "01_foundations/part.tex" in chapters_content
        assert "01_basic_concepts/chapter.tex" in chapters_content
        
        # Check section file includes are in chapters_index
        for i in range(1, 11):
            assert f"01_basic_concepts/1-{i}.tex" in chapters_content
    
    def test_multiple_parts_ordered(self, tmp_path):
        """Test generation with multiple parts in correct order."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = _make_intro_parts_tree(intro_dir)
        parts_root = parts_dir / "parts"
        
        # Create parts out of order
        for part_num, part_name in [(3, "third"), (1, "first"), (2, "second")]:
            part_dir = parts_root / f"0{part_num}_{part_name}"
            part_dir.mkdir()
            (part_dir / "part.tex").write_text(f"\\part{{{part_name.title()}}}\n")
            
            chapters_dir = part_dir / "chapters"
            chapters_dir.mkdir()
            
            # Create one chapter per part
            chapter_dir = chapters_dir / "01_intro"
            chapter_dir.mkdir()
            (chapter_dir / "chapter.tex").write_text(f"\\chapter{{Introduction to {part_name.title()}}}\n")
            
            # Create a few section files
            for i in range(1, 4):
                (chapter_dir / f"1-{i}.tex").write_text(f"% Content {i}\n")
        
        # Generate chapters_index
        chapters_output = generate_chapters_index(intro_dir)
        chapters_content = chapters_output.read_text()
        
        # Check parts appear in order
        first_pos = chapters_content.find("01_first/part.tex")
        second_pos = chapters_content.find("02_second/part.tex")
        third_pos = chapters_content.find("03_third/part.tex")
        
        assert first_pos < second_pos < third_pos
    
    def test_multiple_chapters_in_part(self, tmp_path):
        """Test generation with multiple chapters in one part."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = _make_intro_parts_tree(intro_dir)
        parts_root = parts_dir / "parts"
        
        # Create a part
        part_dir = parts_root / "01_main"
        part_dir.mkdir()
        (part_dir / "part.tex").write_text("\\part{Main}\n")
        
        chapters_dir = part_dir / "chapters"
        chapters_dir.mkdir()
        
        # Create chapters out of order
        for chapter_num, chapter_name in [(3, "third"), (1, "first"), (2, "second")]:
            chapter_dir = chapters_dir / f"0{chapter_num}_{chapter_name}"
            chapter_dir.mkdir()
            (chapter_dir / "chapter.tex").write_text(f"\\chapter{{{chapter_name.title()}}}\n")
            
            for i in range(1, 3):
                (chapter_dir / f"{chapter_num}-{i}.tex").write_text(f"% Content\n")
        
        # Generate chapters_index
        chapters_output = generate_chapters_index(intro_dir)
        chapters_content = chapters_output.read_text()
        
        # Check chapters appear in order
        first_pos = chapters_content.find("01_first/chapter.tex")
        second_pos = chapters_content.find("02_second/chapter.tex")
        third_pos = chapters_content.find("03_third/chapter.tex")
        
        assert first_pos < second_pos < third_pos
    
    def test_build_directory_created(self, tmp_path):
        """Test that build directory is created if it doesn't exist."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        _make_intro_parts_tree(intro_dir)
        
        assert not (intro_dir / "build").exists()
        
        output = generate_introduction_index(intro_dir)
        
        assert output.parent.exists()
        assert output.parent.name == "build"


class TestAppendixSupport:
    """Test appendix support in index generation."""
    
    def test_no_appendix_directory(self, tmp_path):
        """Test that no appendix code is generated when appendix/ doesn't exist."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        _make_intro_parts_tree(intro_dir)
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should not contain \appendix
        assert "\\appendix" not in content
    
    def test_appendix_with_files(self, tmp_path):
        """Test that appendix files are included after chapters."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = _make_intro_parts_tree(intro_dir)
        parts_root = parts_dir / "parts"
        appendix_dir = parts_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create a part with chapter
        part_dir = parts_root / "01_main"
        part_dir.mkdir()
        (part_dir / "part.tex").write_text("\\part{Main}\n")
        
        chapters_dir = part_dir / "chapters"
        chapters_dir.mkdir()
        
        chapter_dir = chapters_dir / "01_intro"
        chapter_dir.mkdir()
        (chapter_dir / "chapter.tex").write_text("\\chapter{Introduction}\n")
        (chapter_dir / "1-1.tex").write_text("% Content\n")
        
        # Create appendix files
        (appendix_dir / "01_notation.tex").write_text("% Notation")
        (appendix_dir / "02_proofs.tex").write_text("% Proofs")
        
        # sections_index.tex is frontmatter-only - appendix goes in chapters_index
        sections_output = generate_introduction_index(intro_dir)
        sections_content = sections_output.read_text()
        
        # sections_index should NOT contain appendix
        assert "\\appendix" not in sections_content
        assert "parts/appendix/" not in sections_content
        
        # Generate chapters_index which should contain the appendix
        chapters_output = generate_chapters_index(intro_dir)
        chapters_content = chapters_output.read_text()
        
        # Should contain \appendix in chapters_index
        assert "\\appendix" in chapters_content
        
        # Should contain appendix includes in chapters_index
        assert "\\input{parts/appendix/01_notation.tex}" in chapters_content
        assert "\\input{parts/appendix/02_proofs.tex}" in chapters_content
        
        # Appendix should come after chapters in chapters_index
        chapter_pos = chapters_content.find("01_intro/chapter.tex")
        appendix_pos = chapters_content.find("\\appendix")
        assert chapter_pos < appendix_pos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
