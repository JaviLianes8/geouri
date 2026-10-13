from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

from geouri._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


def _run(argv: list[str], stdin: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, stdin=io.StringIO(stdin), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def test_prints_the_canonical_form_of_each_argument() -> None:
    code, out, err = _run(["GEO:48.2010,16.3695;CRS=WGS84;U=40", "geo:90,12"])
    assert (code, out, err) == (0, "geo:48.201,16.3695;u=40\ngeo:90,0\n", "")


def test_reads_lines_from_stdin_and_skips_blank_ones() -> None:
    code, out, _ = _run([], "geo:1,2\r\n\ngeo:3.50,4\n")
    assert (code, out) == (0, "geo:1,2\ngeo:3.5,4\n")


def test_reports_invalid_uris_and_exits_one() -> None:
    code, out, err = _run(["geo:1,2", "geo:94,0", "geo:1,2?z=3"])
    assert code == 1
    assert out == "geo:1,2\n"
    assert err == "invalid (latitude-range): geo:94,0\ninvalid (query): geo:1,2?z=3\n"


def test_json_output_lists_every_field() -> None:
    code, out, _ = _run(["--json", "geo:1,2,3;u=4;n=caf%C3%A9;f"])
    assert code == 0
    assert json.loads(out) == {
        "uri": "geo:1,2,3;u=4;n=caf%C3%A9;f",
        "lat": 1.0,
        "lon": 2.0,
        "alt": 3.0,
        "uncertainty": 4.0,
        "crs": "wgs84",
        "params": {"n": "caf\u00e9", "f": None},
    }


def test_android_mode_prints_json() -> None:
    code, out, _ = _run(["--android", "geo:0,0?q=1,2(Home)&z=5"])
    assert code == 0
    data = json.loads(out)
    assert (data["zoom"], data["label"], data["query"], data["extras"]) == (5, "Home", None, {})
    assert (data["point"]["uri"], data["pin"]["uri"]) == ("geo:0,0", "geo:1,2")


def test_android_mode_reports_invalid_input() -> None:
    assert _run(["--android", "geo:1,2?z=99"]) == (1, "", "invalid (zoom): geo:1,2?z=99\n")


def test_invalid_input_is_printed_with_control_characters_escaped() -> None:
    code, _, err = _run([], "geo:1,2;x=\x1b[31m\n")
    assert code == 1
    assert err == "invalid (param-value): geo:1,2;x=\\x1b[31m\n"


def test_usage_errors_exit_two_on_the_given_streams() -> None:
    code, out, err = _run(["--bogus"])
    assert (code, out) == (2, "")
    assert "unrecognized arguments: --bogus" in err


def test_help_goes_to_the_given_stdout() -> None:
    code, out, _ = _run(["--help"])
    assert code == 0
    assert "--android" in out


def test_runs_as_a_module() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "geouri", "geo:1.0,2"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert (result.returncode, result.stdout) == (0, "geo:1,2\n"), result.stderr
