"""Installed CLI encoding checks shared by wheel and sdist consumers."""

from __future__ import annotations

import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path


def check_encoding(python: Path, script: Path, work: Path) -> None:
    number = "1.123456789012345678901"
    for command in ([str(python), "-m", "geouri"], [str(script)]):
        for android in (False, True):
            uri = f"geo:{number},2;name=%E6%9D%B1%E4%BA%AC"
            if android:
                uri += "?q=%E6%9D%B1%E4%BA%AC"
            result = subprocess.run(
                [*command, "--android" if android else "--json", uri],
                cwd=work,
                env={**os.environ, "PYTHONPATH": "", "PYTHONIOENCODING": "cp1252:strict"},
                capture_output=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr
            assert result.stderr == b""
            data = json.loads(result.stdout.decode("ascii"), parse_float=Decimal)
            point = data["point"] if android else data
            assert point["lat"] == Decimal(number)
            assert point["params"] == {"name": "\u6771\u4eac"}
            if android:
                assert data["query"] == "\u6771\u4eac"
