"""Command line: print the canonical form of each geo: URI, exit 1 if any is invalid."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import Any, NoReturn, TextIO

from ._android import AndroidGeo, parse_android
from ._errors import GeoURIError
from ._grammar import plain
from ._model import GeoURI
from ._parse import parse


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(2, "geouri: invalid command-line arguments\n")


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
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
    uris: Iterable[str | None] = args.uris or _lines(stdin or sys.stdin)
    status = 0
    for uri in uris:
        if uri is None:
            err.write("invalid (encoding)\n")
            status = 1
            continue
        try:
            if args.android:
                line = _json(_android(parse_android(uri)))
            else:
                parsed = parse(uri)
                line = _json(_fields(parsed)) if args.json else str(parsed)
        except GeoURIError as error:
            err.write(f"invalid ({error.reason})\n")
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
        items = (f"{json.dumps(k)}: {_json(v)}" for k, v in value.items())
        return "{" + ", ".join(items) + "}"
    return json.dumps(value)


def _lines(stream: TextIO) -> Iterable[str | None]:
    # Decode raw lines separately so text read-ahead cannot discard a valid batch.
    lines: Iterable[bytes] | Iterable[str] = getattr(stream, "buffer", stream)
    for line in lines:
        if isinstance(line, bytes):
            try:
                line = line.decode(stream.encoding, errors="strict")
            except UnicodeDecodeError:
                yield None
                continue
        text = line.rstrip("\r\n")
        if text:
            yield text
