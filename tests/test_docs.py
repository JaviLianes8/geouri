"""The README examples run and print what their comments say; docs and versions agree."""

from __future__ import annotations

import contextlib
import io
import os
import re
import subprocess
import sys
import typing
from pathlib import Path

import geouri

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _python_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL)


def test_every_readme_example_runs_and_prints_its_comment() -> None:
    checked = 0
    for block in _python_blocks():
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
        expected = re.findall(r"^print\(.*\)  # (.+)$", block, flags=re.MULTILINE)
        assert expected, block
        assert out.getvalue().splitlines() == expected
        checked += len(expected)
    assert len(_python_blocks()) == 5
    assert checked >= 25


def test_the_command_line_example_prints_what_the_readme_shows() -> None:
    block = README.split("### Command line", 1)[1].split("```", 2)[1]
    command, *shown = block.strip().splitlines()
    args = re.findall(r'"([^"]+)"', command)
    result = subprocess.run(
        [sys.executable, "-m", "geouri", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT / "src",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 1
    assert result.stdout.splitlines() + result.stderr.splitlines() == shown


def test_the_api_table_lists_every_public_name() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in geouri.__all__:
        assert f"`{name}" in table, name


def test_the_readme_lists_every_reason_in_order() -> None:
    section = README.split("### Reasons", 1)[1].split("\n## ", 1)[0]
    listed = re.findall(r"^- `([a-z-]+)`", section, flags=re.MULTILINE)
    assert listed == list(typing.get_args(geouri.Reason))


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == geouri.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{geouri.__version__}]" in text


def test_no_em_dash_anywhere_in_the_tree() -> None:
    suffixes = {".py", ".md", ".toml", ".json", ".ps1", ".txt"}
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if path.is_file() and path.suffix in suffixes and not parts[0].startswith("."):
            if parts[:2] == ("tests", "upstream") and path.name != "MANIFEST.json":
                continue  # fetched third-party text, not ours
            assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*ROOT.joinpath("src").rglob("*.py"), *ROOT.joinpath("tests").rglob("*.py")]:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path
