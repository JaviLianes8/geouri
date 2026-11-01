"""Hand-written installed contracts for record counts and query whitespace."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def check_records(command: list[str], work: Path) -> None:
    for args in ([], ["--json"], ["--android"]):
        expected = ["geo:3,4", "geo:1,2", "geo:1,2", "geo:5,6", "geo:1,2"]
        result = _run(command, work, args, ("\n".join(expected) + "\n").encode())
        assert result.returncode == 0, result.stderr
        assert result.stderr == b""
        assert _uris(result.stdout, args) == expected

        data = b"geo:3,4\n\xff\ngeo:1,2\n\xff\xff\ngeo:5,6\n\xff\n"
        result = _run(command, work, args, data)
        assert result.returncode == 1
        assert result.stderr.decode().splitlines() == ["invalid (encoding)"] * 3
        assert _uris(result.stdout, args) == ["geo:3,4", "geo:1,2", "geo:5,6"]

    for query in ("Main\tStreet", " Main\t\tStreet ", "\tMain Street\t"):
        result = _run(command, work, ["--android"], f"geo:0,0?q={query}\n".encode())
        assert result.returncode == 0, result.stderr
        assert result.stderr == b""
        records = [json.loads(line) for line in result.stdout.decode().splitlines()]
        assert len(records) == 1
        assert records[0]["query"] == query


def _run(
    command: list[str], work: Path, args: list[str], data: bytes
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [*command, *args],
        input=data,
        cwd=work,
        env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": "utf-8:strict"},
        capture_output=True,
        timeout=30,
    )


def _uris(output: bytes, args: list[str]) -> list[str]:
    lines = output.decode().splitlines()
    if not args:
        return lines
    records = [json.loads(line) for line in lines]
    if args == ["--android"]:
        return [record["point"]["uri"] for record in records]
    return [record["uri"] for record in records]
