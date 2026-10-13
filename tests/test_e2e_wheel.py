"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with GEOURI_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("GEOURI_E2E") != "1", reason="set GEOURI_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pickle
from decimal import Decimal
import geouri
from geouri import GeoURIError, build, build_android, compare, parse, parse_android

assert "site-packages" in geouri.__file__, geouri.__file__
assert importlib.metadata.version("geouri") == geouri.__version__
assert importlib.resources.files("geouri").joinpath("py.typed").is_file()
uri = parse("GEO:48.2010,16.3695,183;CRS=WGS84;U=40;Name=caf%C3%A9")
assert str(uri) == "geo:48.201,16.3695,183;u=40;name=caf%C3%A9"
assert uri.params["name"] == "caf\u00e9"
assert parse("geo:90,-22.43;crs=WGS84") == parse("geo:90,46")
assert parse("geo:10,180") == parse("geo:10,-180")
assert compare(parse("geo:22,0;bar=Blue"), parse("geo:22,0;BAR=blue")) is None
assert build(Decimal("0.10000000000000000001"), 1e-7) == "geo:0.10000000000000000001,0.0000001"
assert build_android(47.6, -122.3, zoom=11) == "geo:47.6,-122.3?z=11"
assert parse_android("geo:0,0?q=34.99,-106.61(Treasure)").label == "Treasure"
for bad, reason in [("geo:94,0", "latitude-range"), ("geo:1,2;u=1;crs=x", "param-order")]:
    try:
        parse(bad)
    except GeoURIError as error:
        assert error.reason == reason
        assert pickle.loads(pickle.dumps(error)).reason == reason
    else:
        raise AssertionError(bad)
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("geouri-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    script = bindir / ("geouri.exe" if sys.platform == "win32" else "geouri")
    cli = _run(script, "geo:1.50,2;CRS=wgs84", "geo:1,2?z=3", cwd=work)
    assert cli.returncode == 1
    assert cli.stdout == "geo:1.5,2\n"
    assert cli.stderr == "invalid (query): geo:1,2?z=3\n"


def test_distributions_ship_no_third_party_text(tmp_path: Path) -> None:
    built = _run(sys.executable, "-m", "build", "--outdir", tmp_path, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = tmp_path.glob("geouri-*.whl")
    (sdist,) = tmp_path.glob("geouri-*.tar.gz")
    wheel_names = zipfile.ZipFile(wheel).namelist()
    assert all(n.startswith(("geouri/", "geouri-")) for n in wheel_names), wheel_names
    with tarfile.open(sdist) as archive:
        names = [n.split("/", 1)[1] for n in archive.getnames() if "/" in n]
    assert "tests/upstream/MANIFEST.json" in names
    assert "tests/data/examples.json" in names
    assert not any(n.endswith("rfc5870.txt") for n in names), names
    assert not any(n.startswith((".github", "IMPROVEMENTS")) for n in names), names
