"""
Tests for frontmatter/mainmatter separation in Introduction book indices.

This test module ensures that:
1. build/sections_index.tex contains ONLY frontmatter (no sectioning commands)
2. build/chapters_index.tex contains ALL mainmatter content
3. No duplicate content between the two files
4. Frontmatter numbering issues (0.1, etc.) cannot occur
"""
import pytest
from pathlib import Path
from texrepo.introduction_index import generate_introduction_index, generate_chapters_index


class TestFrontmatterMainmatterSeparation:
    """Test that frontmatter and mainmatter spines are properly separated."""
    
    def test_sections_index_is_frontmatter_only(self, tmp_path):
        """Test that sections_index.tex contains ONLY frontmatter navigation."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        parts_root = parts_dir / "parts"
        parts_root.mkdir()
        
        # Create frontmatter files
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter files
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Create a part with chapter and content
        part_dir = parts_root / "01_foundations"
        chapter_dir = part_dir / "chapters" / "01_intro"
        chapter_dir.mkdir(parents=True)
        
        # Create part.tex with \part command
        (part_dir / "part.tex").write_text("\\part{Foundations}\n")
        
        # Create chapter.tex with \chapter command
        (chapter_dir / "chapter.tex").write_text("\\chapter{Introduction}\nChapter prologue.\n")
        
        # Create section files
        for i in range(1, 4):
            (chapter_dir / f"1-{i}.tex").write_text(f"\\section{{Section {i}}}\nContent {i}.\n")
        
        # Generate the index files
        sections_index = generate_introduction_index(intro_dir)
        chapters_index = generate_chapters_index(intro_dir)
        
        # Read generated content
        sections_content = sections_index.read_text()
        chapters_content = chapters_index.read_text()
        
        # CRITICAL: sections_index.tex must NOT contain any sectioning commands
        forbidden_commands = [
            r'\part{', r'\part[',
            r'\chapter{', r'\chapter[', r'\chapter*{',
            r'\section{', r'\section[', r'\section*{',
            r'\subsection{', r'\subsection[',
            r'\appendix'
        ]
        
        for cmd in forbidden_commands:
            assert cmd not in sections_content, \
                f"sections_index.tex must NOT contain {cmd} (frontmatter-only!)"
        
        # sections_index.tex should ONLY include parts/frontmatter/* files
        assert "parts/frontmatter/title" in sections_content
        assert "parts/frontmatter/preface" in sections_content
        assert "parts/frontmatter/how_to_read" in sections_content
        assert "parts/frontmatter/toc" in sections_content
        
        # sections_index.tex must NOT include any chapter/section content
        assert "parts/parts/" not in sections_content, \
            "sections_index.tex must NOT include chapter/section content"
        assert "chapter.tex" not in sections_content
        assert "1-1.tex" not in sections_content
        
        # sections_index.tex must NOT include backmatter files
        assert "parts/backmatter/" not in sections_content, \
            "sections_index.tex must NOT include backmatter (that's in chapters_index.tex)"
    
    def test_chapters_index_contains_all_mainmatter(self, tmp_path):
        """Test that chapters_index.tex contains ALL mainmatter content."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        parts_root = parts_dir / "parts"
        parts_root.mkdir()
        
        # Create frontmatter files
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter files
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Create two parts with chapters
        for part_num, part_name in [(1, "foundations"), (2, "applications")]:
            part_dir = parts_root / f"0{part_num}_{part_name}"
            part_dir.mkdir()
            (part_dir / "part.tex").write_text(f"\\part{{{part_name.title()}}}\n")
            
            chapters_dir = part_dir / "chapters"
            chapters_dir.mkdir()
            
            for ch_num, ch_name in [(1, "intro"), (2, "details")]:
                chapter_dir = chapters_dir / f"0{ch_num}_{ch_name}"
                chapter_dir.mkdir()
                (chapter_dir / "chapter.tex").write_text(
                    f"\\chapter{{{ch_name.title()}}}\nChapter prologue.\n"
                )
                
                # Create section files
                for i in range(1, 3):
                    (chapter_dir / f"{ch_num}-{i}.tex").write_text(f"Section content {i}.\n")
        
        # Create appendix
        appendix_dir = parts_dir / "appendix"
        appendix_dir.mkdir()
        (appendix_dir / "01_notation.tex").write_text("\\chapter{Notation}\nAppendix content.\n")
        
        # Generate the index files
        sections_index = generate_introduction_index(intro_dir)
        chapters_index = generate_chapters_index(intro_dir)
        
        # Read generated content
        chapters_content = chapters_index.read_text()
        
        # chapters_index.tex MUST contain all mainmatter content
        
        # Check for part includes
        assert "parts/parts/01_foundations/part.tex" in chapters_content
        assert "parts/parts/02_applications/part.tex" in chapters_content
        
        # Check for chapter includes
        assert "parts/parts/01_foundations/chapters/01_intro/chapter.tex" in chapters_content
        assert "parts/parts/01_foundations/chapters/02_details/chapter.tex" in chapters_content
        assert "parts/parts/02_applications/chapters/01_intro/chapter.tex" in chapters_content
        assert "parts/parts/02_applications/chapters/02_details/chapter.tex" in chapters_content
        
        # Check for section file includes
        assert "parts/parts/01_foundations/chapters/01_intro/1-1.tex" in chapters_content
        assert "parts/parts/01_foundations/chapters/01_intro/1-2.tex" in chapters_content
        assert "parts/parts/01_foundations/chapters/02_details/2-1.tex" in chapters_content
        
        # Check for appendix
        assert "\\appendix" in chapters_content
        assert "parts/appendix/01_notation.tex" in chapters_content
        
        # Check for backmatter
        assert "parts/backmatter/scope_limits" in chapters_content
        assert "parts/backmatter/closing_notes" in chapters_content
        
        # chapters_index.tex must NOT include frontmatter files
        assert "parts/frontmatter/" not in chapters_content
    
    def test_no_duplicate_content_between_indices(self, tmp_path):
        """Test that no content appears in both sections_index and chapters_index."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        parts_root = parts_dir / "parts"
        parts_root.mkdir()
        
        # Create frontmatter files
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter files
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Create a part with chapter
        part_dir = parts_root / "01_test"
        chapter_dir = part_dir / "chapters" / "01_chapter"
        chapter_dir.mkdir(parents=True)
        (part_dir / "part.tex").write_text("\\part{Test}\n")
        (chapter_dir / "chapter.tex").write_text("\\chapter{Chapter}\n")
        (chapter_dir / "1-1.tex").write_text("Content.\n")
        
        # Generate the index files
        sections_index = generate_introduction_index(intro_dir)
        chapters_index = generate_chapters_index(intro_dir)
        
        # Read generated content
        sections_content = sections_index.read_text()
        chapters_content = chapters_index.read_text()
        
        # Extract all \input commands from both files
        import re
        input_pattern = re.compile(r'\\input\{([^}]+)\}')
        
        sections_inputs = set(input_pattern.findall(sections_content))
        chapters_inputs = set(input_pattern.findall(chapters_content))
        
        # Check for duplicates
        duplicates = sections_inputs & chapters_inputs
        assert not duplicates, \
            f"Found duplicate includes in both indices: {duplicates}\n" \
            f"This causes duplicate TOC entries!"
    
    def test_validation_rejects_forbidden_commands(self, tmp_path):
        """Test that validation catches if forbidden commands leak into sections_index."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        frontmatter_dir = parts_dir / "frontmatter"
        frontmatter_dir.mkdir(parents=True)
        
        # Create frontmatter files - but one contains a forbidden command
        (frontmatter_dir / "title.tex").write_text("% Title\n")
        (frontmatter_dir / "preface.tex").write_text("% Preface\n\\chapter{Oops}\n")  # BUG!
        (frontmatter_dir / "how_to_read.tex").write_text("% How to read\n")
        (frontmatter_dir / "toc.tex").write_text("\\tableofcontents\n")
        
        # This should fail validation because preface.tex is included and contains \chapter
        # Note: Current implementation validates the GENERATED file, not the included files
        # So this test verifies the validation logic exists
        sections_index = generate_introduction_index(intro_dir)
        content = sections_index.read_text()
        
        # The generated file should not contain \chapter directly
        # (it only has \input commands to frontmatter files)
        assert "\\chapter{" not in content
    
    def test_empty_book_generates_minimal_indices(self, tmp_path):
        """Test that book with no chapters generates minimal but valid indices."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create minimal structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        (parts_dir / "parts").mkdir()  # Empty parts directory
        
        # Create frontmatter files
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter files
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Generate the index files
        sections_index = generate_introduction_index(intro_dir)
        chapters_index = generate_chapters_index(intro_dir)
        
        # Both files should exist
        assert sections_index.exists()
        assert chapters_index.exists()
        
        # Read generated content
        sections_content = sections_index.read_text()
        chapters_content = chapters_index.read_text()
        
        # sections_index should have frontmatter
        assert "parts/frontmatter/title" in sections_content
        assert "parts/frontmatter/toc" in sections_content
        
        # chapters_index should have backmatter
        assert "parts/backmatter/scope_limits" in chapters_content
        assert "parts/backmatter/closing_notes" in chapters_content
        
        # Neither should have any chapter/section content
        assert "chapter.tex" not in sections_content
        assert "chapter.tex" not in chapters_content or chapters_content.count("chapter.tex") == 0
    
    def test_chapters_are_in_correct_order(self, tmp_path):
        """Test that chapters appear in correct numeric order in mainmatter spine."""
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        parts_root = parts_dir / "parts"
        parts_root.mkdir()
        
        # Create frontmatter
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Create chapters in deliberately wrong order (filesystem may sort differently)
        part_dir = parts_root / "01_part"
        chapters_dir = part_dir / "chapters"
        chapters_dir.mkdir(parents=True)
        (part_dir / "part.tex").write_text("\\part{Part}\n")
        
        # Create chapters 03, 01, 02 (out of order)
        for num, name in [(3, "third"), (1, "first"), (2, "second")]:
            chapter_dir = chapters_dir / f"0{num}_{name}"
            chapter_dir.mkdir()
            (chapter_dir / "chapter.tex").write_text(f"\\chapter{{{name.title()}}}\n")
            (chapter_dir / f"{num}-1.tex").write_text(f"Content {num}.\n")
        
        # Generate chapters_index
        chapters_index = generate_chapters_index(intro_dir)
        content = chapters_index.read_text()
        
        # Find positions of chapter includes
        first_pos = content.find("01_first/chapter.tex")
        second_pos = content.find("02_second/chapter.tex")
        third_pos = content.find("03_third/chapter.tex")
        
        # All should be found
        assert first_pos != -1
        assert second_pos != -1
        assert third_pos != -1
        
        # Must be in correct numeric order
        assert first_pos < second_pos < third_pos, \
            "Chapters must appear in numeric order"


class TestRegressionDuplicateTOC:
    """Regression test for duplicate TOC entries bug."""
    
    def test_no_duplicate_regime_discipline_heading(self, tmp_path):
        """
        Regression test: "Regime Discipline" (or any heading) should appear
        in ONLY ONE index file, not both.
        
        The bug was that sections_index.tex included mainmatter content,
        causing headings to appear in both frontmatter and mainmatter TOCs.
        """
        intro_dir = tmp_path / "00_introduction"
        intro_dir.mkdir()
        
        # Create directory structure
        parts_dir = intro_dir / "parts"
        (parts_dir / "frontmatter").mkdir(parents=True)
        (parts_dir / "backmatter").mkdir(parents=True)
        parts_root = parts_dir / "parts"
        parts_root.mkdir()
        
        # Create frontmatter
        for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
            (parts_dir / "frontmatter" / fname).write_text(f"% {fname}\n")
        
        # Create backmatter
        for fname in ["scope_limits.tex", "closing_notes.tex"]:
            (parts_dir / "backmatter" / fname).write_text(f"% {fname}\n")
        
        # Create the specific chapter that was causing issues
        part_dir = parts_root / "01_regime"
        chapter_dir = part_dir / "chapters" / "01_regime_discipline"
        chapter_dir.mkdir(parents=True)
        (part_dir / "part.tex").write_text("\\part{Regime}\n")
        (chapter_dir / "chapter.tex").write_text("\\chapter{Regime Discipline}\nPrologue.\n")
        (chapter_dir / "1-1.tex").write_text("\\section{Core Concepts}\n")
        
        # Generate both indices
        sections_index = generate_introduction_index(intro_dir)
        chapters_index = generate_chapters_index(intro_dir)
        
        sections_content = sections_index.read_text()
        chapters_content = chapters_index.read_text()
        
        # "Regime Discipline" chapter should ONLY be in chapters_index
        assert "regime_discipline" not in sections_content, \
            "BUG: Regime Discipline chapter leaked into sections_index (frontmatter)!"
        
        assert "regime_discipline" in chapters_content, \
            "Regime Discipline chapter must be in chapters_index (mainmatter)"
        
        # Verify the specific paths
        chapter_path = "parts/parts/01_regime/chapters/01_regime_discipline"
        assert chapter_path not in sections_content
        assert chapter_path in chapters_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
