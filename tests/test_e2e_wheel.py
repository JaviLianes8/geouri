"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with GEOURI_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest
from wheel_consumer import CHANGES, SNAPSHOT

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
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False, timeout=240
    )


@pytest.mark.parametrize("upgrade", [False, True])
def test_installed_wheel_end_to_end(tmp_path: Path, upgrade: bool) -> None:
    if upgrade and os.environ.get("GEOURI_E2E_PYPI") != "1":
        pytest.skip("set GEOURI_E2E_PYPI=1 for the live PyPI upgrade")
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("geouri-*.whl")

    env_dir = tmp_path / "venv"
    import venv

    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    work = tmp_path / "work"
    work.mkdir()
    before = ""
    if upgrade:
        old = _run(
            python,
            "-m",
            "pip",
            "install",
            "--index-url",
            "https://pypi.org/simple",
            "geouri==0.2.0",
        )
        assert old.returncode == 0, old.stderr
        snapshot = _run(python, "-I", "-c", SNAPSHOT, cwd=work)
        assert snapshot.returncode == 0, snapshot.stderr
        before = snapshot.stdout
        changes = _run(python, "-I", "-c", CHANGES, "0.2.0", cwd=work)
        assert changes.returncode == 0, changes.stderr
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"

    script = bindir / ("geouri.exe" if sys.platform == "win32" else "geouri")
    cli = _run(script, "geo:1.50,2;CRS=wgs84", "geo:1,2?z=3", cwd=work)
    assert cli.returncode == 1
    assert cli.stdout == "geo:1.5,2\n"
    assert cli.stderr == "invalid (query)\n"
    android = _run(script, "--android", "geo:0,0?q=Main+Street&z=3", cwd=work)
    assert android.returncode == 0 and '"query": "Main Street"' in android.stdout
    module = _run(python, "-I", "-m", "geouri", "--json", "geo:1,2", cwd=work)
    assert module.returncode == 0 and '"lat": 1' in module.stdout
    usage = _run(script, "--unknown", cwd=work)
    assert usage.returncode == 2 and "--unknown" not in usage.stderr
    if upgrade:
        snapshot = _run(python, "-I", "-c", SNAPSHOT, cwd=work)
        assert snapshot.returncode == 0, snapshot.stderr
        assert snapshot.stdout == before
        changes = _run(python, "-I", "-c", CHANGES, "1.0.0", cwd=work)
        assert changes.returncode == 0, changes.stderr


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
    assert {"LICENSE", "README.md", "GUIDE.md", "CHANGELOG.md", "pyproject.toml"} <= set(names)
    assert "geouri/py.typed" in wheel_names
    assert any(n.endswith("/licenses/LICENSE") for n in wheel_names)
    assert not any("__pycache__" in n or n.endswith((".pyc", ".html")) for n in names)
    assert not any(n.startswith(("tests/", "scripts/")) for n in wheel_names)
    metadata = zipfile.ZipFile(wheel).read("geouri-1.0.0.dist-info/METADATA").decode()
    assert "Development Status :: 5 - Production/Stable" in metadata
    assert "Requires-Python: >=3.10" in metadata
    assert not any(
        line.startswith("Requires-Dist:") and "extra ==" not in line
        for line in metadata.splitlines()
    )
