"""
Tests for the new parts/ structure in introduction book.
Tests both new parts/ structure and backward compatibility with old structure.
"""
import pytest
from pathlib import Path

from texrepo.introduction_index import generate_introduction_index, generate_chapters_index


class TestPartsStructure:
    """Test the new parts/ container structure."""
    
    def test_new_structure_sections_index(self, tmp_path):
        """Test that generator works with new parts/sections/ structure."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = intro_dir / "parts"
        parts_dir.mkdir()
        sections_dir = parts_dir / "sections"
        sections_dir.mkdir()
        
        # Create a section
        section_dir = sections_dir / "01_framing"
        section_dir.mkdir()
        for i in range(1, 4):
            (section_dir / f"1-{i}.tex").write_text(f"% Content {i}")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use parts/sections prefix and formatted title
        assert r"\section{Framing}" in content
        assert r"\input{parts/sections/01_framing/1-1.tex}" in content
        assert r"\input{parts/sections/01_framing/1-2.tex}" in content
        assert r"\input{parts/sections/01_framing/1-3.tex}" in content
    
    def test_new_structure_appendix(self, tmp_path):
        """Test that generator works with new parts/appendix/ structure."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = intro_dir / "parts"
        (parts_dir / "sections").mkdir(parents=True)
        appendix_dir = parts_dir / "appendix"
        appendix_dir.mkdir()
        
        # Create appendix files
        (appendix_dir / "01_notation.tex").write_text("% Notation")
        (appendix_dir / "02_proofs.tex").write_text("% Proofs")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Should use parts/appendix prefix
        assert r"\appendix" in content
        assert r"\input{parts/appendix/01_notation.tex}" in content
        assert r"\input{parts/appendix/02_proofs.tex}" in content
    
    def test_new_structure_chapters_index(self, tmp_path):
        """Test that chapters index works with new parts/sections/ structure."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = intro_dir / "parts"
        sections_dir = parts_dir / "sections"
        sections_dir.mkdir(parents=True)
        
        # Create sections with chapter.tex
        for n, name in [(1, "first"), (2, "second")]:
            section_dir = sections_dir / f"0{n}_{name}"
            section_dir.mkdir()
            (section_dir / "chapter.tex").write_text("% chapter")
        
        output = generate_chapters_index(intro_dir)
        content = output.read_text()
        
        # Should use parts/sections prefix
        assert r"\input{parts/sections/01_first/chapter.tex}" in content
        assert r"\input{parts/sections/02_second/chapter.tex}" in content
    
    def test_legacy_structure_rejected(self, tmp_path):
        """Test that legacy structure (sections at top level) is rejected."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create legacy structure (sections at intro_dir level, not under parts/)
        sections_dir = intro_dir / "sections"
        sections_dir.mkdir()
        section_dir = sections_dir / "01_test"
        section_dir.mkdir()
        (section_dir / "1-1.tex").write_text("% Content")
        
        # Should fail because parts/ directory is missing
        try:
            output = generate_introduction_index(intro_dir)
            # If we get here, it should have raised an error
            assert False, "Expected SystemExit or error for legacy structure"
        except SystemExit:
            # Expected behavior - legacy structure is rejected
            pass
    
    def test_multiple_sections_new_structure(self, tmp_path):
        """Test multiple sections with new parts/ structure in correct order."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        sections_dir = intro_dir / "parts" / "sections"
        sections_dir.mkdir(parents=True)
        
        # Create sections out of order
        for n, name in [(3, "third"), (1, "first"), (2, "second")]:
            section_dir = sections_dir / f"0{n}_{name}"
            section_dir.mkdir()
            (section_dir / f"{n}-1.tex").write_text(f"% Content {n}")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Check sections appear in order (now formatted as title case)
        first_pos = content.find(r"\section{First}")
        second_pos = content.find(r"\section{Second}")
        third_pos = content.find(r"\section{Third}")
        
        assert first_pos < second_pos < third_pos
    
    def test_new_structure_appendix_after_sections(self, tmp_path):
        """Test that appendix comes after sections in new structure."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        parts_dir = intro_dir / "parts"
        parts_dir.mkdir()
        
        sections_dir = parts_dir / "sections"
        sections_dir.mkdir()
        section = sections_dir / "01_intro"
        section.mkdir()
        (section / "1-1.tex").write_text("% Intro")
        
        appendix_dir = parts_dir / "appendix"
        appendix_dir.mkdir()
        (appendix_dir / "01_notation.tex").write_text("% Notation")
        
        output = generate_introduction_index(intro_dir)
        content = output.read_text()
        
        # Verify order: section first, then appendix
        section_pos = content.find(r"\input{parts/sections/01_intro/1-1.tex}")
        appendix_pos = content.find(r"\appendix")
        
        assert section_pos < appendix_pos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
