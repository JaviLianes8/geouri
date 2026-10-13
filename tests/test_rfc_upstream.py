"""The committed RFC examples are exactly the geo: URIs printed in the fetched RFC text.

Skips until `python scripts/fetch_upstream.py` has fetched rfc5870.txt.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from conftest import read_upstream

DATA = json.loads((Path(__file__).parent / "data" / "examples.json").read_text("utf-8"))


def _uris_in(text: str) -> list[str]:
    # Drop page headers and footers so a URI wrapped across a page break joins up.
    lines = [
        line
        for line in text.replace("\f", "").splitlines()
        if not re.match(r"^(RFC 5870 |Mayrhofer & Spanring)", line)
    ]
    body = "\n".join(lines)
    pattern = re.compile(r"<(geo:[^>]*)>|'(geo:[^']*)'|^\s*(geo:\S+)\s*$", re.MULTILINE)
    found = []
    for match in pattern.finditer(body):
        uri = re.sub(r"\s+", "", next(group for group in match.groups() if group))
        if "%lat%" not in uri:  # section 7 templates, not URIs
            found.append(uri)
    return found


def test_the_examples_match_the_rfc_text() -> None:
    text = read_upstream("rfc5870.txt").decode("ascii")
    assert _uris_in(text) == DATA["rfc5870_uris"]


def test_the_manifest_and_the_examples_name_the_same_text() -> None:
    folder = Path(__file__).parent / "upstream"
    manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["rfc5870.txt"]["sha256"] == DATA["sources"]["rfc5870"]["sha256"]
