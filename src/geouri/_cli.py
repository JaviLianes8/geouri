"""Command line: print the canonical form of each geo: URI, exit 1 if any is invalid."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import Any, TextIO

from ._android import AndroidGeo, parse_android
from ._errors import GeoURIError
from ._grammar import plain
from ._model import GeoURI
from ._parse import parse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geouri",
        description="Validate geo: URIs (RFC 5870) and print their canonical form. "
        "Reads one URI per line from standard input when none are given.",
    )
    parser.add_argument("uris", nargs="*", metavar="URI")
    parser.add_argument("--json", action="store_true", help="print one JSON object per URI")
    parser.add_argument(
        "--android", action="store_true", help="read the Android map intent form (prints JSON)"
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the command line and return its exit status (0 ok, 1 invalid, 2 usage)."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            args = _parser().parse_args(argv)
    except SystemExit as stop:
        return int(stop.code or 0)
    uris: Iterable[str] = args.uris or _lines(stdin or sys.stdin)
    status = 0
    for uri in uris:
        try:
            if args.android:
                line = _json(_android(parse_android(uri)))
            else:
                parsed = parse(uri)
                line = _json(_fields(parsed)) if args.json else str(parsed)
        except GeoURIError as error:
            err.write(f"invalid ({error.reason}): {_shown(uri)}\n")
            status = 1
            continue
        out.write(line + "\n")
    return status


def _fields(uri: GeoURI) -> dict[str, Any]:
    lat, lon, alt, unc = uri._exact
    return {
        "uri": str(uri),
        "lat": lat,
        "lon": lon,
        "alt": alt,
        "uncertainty": unc,
        "crs": uri.crs,
        "params": dict(uri.params),
    }


def _android(geo: AndroidGeo) -> dict[str, Any]:
    return {
        "point": _fields(geo.point),
        "zoom": geo.zoom,
        "query": geo.query,
        "pin": None if geo.pin is None else _fields(geo.pin),
        "label": geo.label,
        "extras": dict(geo.extras),
    }


def _json(value: Any) -> str:
    """JSON with numbers written as their exact decimal text, never rounded or infinite."""
    if isinstance(value, Decimal):
        return plain(value)
    if isinstance(value, dict):
        items = (f"{json.dumps(k, ensure_ascii=False)}: {_json(v)}" for k, v in value.items())
        return "{" + ", ".join(items) + "}"
    return json.dumps(value, ensure_ascii=False)


def _lines(stream: TextIO) -> Iterable[str]:
    for line in stream:
        text = line.rstrip("\r\n")
        if text:
            yield text


def _shown(uri: str) -> str:
    """The input as safe to print: control and other unprintable characters escaped."""
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in uri)
