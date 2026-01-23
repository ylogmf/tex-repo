from pathlib import Path

from texrepo.build_cmd import (
    find_appendix_files,
    inject_appendix_into_entry,
    write_appendix_include,
)


def _sample_entry(tmp_path: Path) -> Path:
    entry = tmp_path / "paper.tex"
    entry.write_text(
        r"""\documentclass{article}
\begin{document}
\input{build/sections_index.tex}
\section{Main Section}
\bibliographystyle{plainnat}
\bibliography{refs}
\end{document}
""",
        encoding="utf-8",
    )
    return entry


def test_no_appendix_directory_is_noop(tmp_path: Path):
    entry = _sample_entry(tmp_path)

    appendix_files = find_appendix_files(tmp_path)
    assert appendix_files == []

    include_path = write_appendix_include(tmp_path, appendix_files)
    assert include_path is None


def test_empty_appendix_directory_is_noop(tmp_path: Path):
    entry = _sample_entry(tmp_path)
    (tmp_path / "appendix").mkdir(parents=True, exist_ok=True)

    appendix_files = find_appendix_files(tmp_path)
    assert appendix_files == []

    include_path = write_appendix_include(tmp_path, appendix_files)
    assert include_path is None


def test_appendix_included_after_sections_index(tmp_path: Path):
    entry = _sample_entry(tmp_path)

    appendix_dir = tmp_path / "appendix"
    appendix_dir.mkdir(parents=True, exist_ok=True)
    (appendix_dir / "02_extra.tex").write_text("% extra\n", encoding="utf-8")
    (appendix_dir / "01_notes.tex").write_text("% notes\n", encoding="utf-8")

    appendix_files = find_appendix_files(tmp_path)
    include_path = write_appendix_include(tmp_path, appendix_files)
    assert include_path is not None

    include_content = include_path.read_text()
    assert include_content.strip().startswith(r"\appendix")
    assert include_content.count(r"\input{appendix/01_notes.tex}") == 1
    assert include_content.count(r"\input{appendix/02_extra.tex}") == 1
    # Order should be stable
    assert include_content.find("appendix/01_notes.tex") < include_content.find(
        "appendix/02_extra.tex"
    )

    injected_entry = inject_appendix_into_entry(entry, include_path)
    injected_text = injected_entry.read_text()

    # Appendix include should appear after the sections index include
    assert injected_text.find("build/sections_index.tex") < injected_text.find(
        "build/texrepo_appendix.tex"
    )
    # And before bibliography
    assert injected_text.find("build/texrepo_appendix.tex") < injected_text.find(
        r"\bibliographystyle"
    )
