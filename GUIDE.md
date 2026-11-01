# geouri guide

Import the ten public names from `geouri`; underscore modules are private.
`__version__` reports the installed release. Python 3.10 or later is required.

## Choose a parser

Use `parse` for the supported RFC 5870 subset and `parse_android` for the Android
query dialect. The RFC parser rejects queries and fragments. Both parsers reject wrong types with
`TypeError`, and malformed values with `GeoURIError`, a `ValueError` subclass.
`Reason` is a `Literal` type alias for the fourteen reasons in the
[README](https://github.com/JaviLianes8/geouri#reasons).

```pycon
>>> from geouri import parse, parse_android
>>> str(parse("GEO:1.50,2;U=4"))
'geo:1.5,2;u=4'
>>> parse_android("geo:0,0?q=Main+Street").query
'Main Street'

```

RFC parameter names are case-insensitive and decoded values are case-sensitive.
Two library policies narrow the RFC grammar: decoded values
must be UTF-8, and names must be unique after case folding. RFC 5870 permits repeated
extension parameters; this library rejects them with `duplicate-param`, even for
identical values or flags, to preserve the one-value-per-name `params` mapping.
Unknown CRS labels are accepted without coordinate range
checks; their semantics are the caller's responsibility. Parameters preserve input
order when printed, so equivalent URIs can print in different parameter orders.

## Exact values and models

`GeoURI(lat, lon, alt=None, uncertainty=None, crs='wgs84', params={})` validates
construction. Public numeric fields are floats; internal exact decimals determine
comparison, hashing, serialization and pickling. Extremely large accepted numbers
can produce infinite float fields, and very small values can underflow; use `str`
or CLI JSON for their exact values. `build` accepts int, float and Decimal values;
booleans, strings and non-finite numbers are rejected.

```pycon
>>> from decimal import Decimal
>>> from geouri import build, compare
>>> build(Decimal("0.10000000000000000001"), 180)
'geo:0.10000000000000000001,180'
>>> compare(parse("geo:90,1"), parse("geo:90,2"))
True
>>> compare(parse("geo:1,2;x=A"), parse("geo:1,2;x=B")) is None
True

```

`compare` returns `None` when all known fields match but unknown parameter names or
decoded values differ, including a parameter present on only one side.
`==` returns false in that case. Missing
altitude and altitude zero differ, as do missing uncertainty and uncertainty zero.
Longitude is ignored at WGS-84 poles; -180 and 180 are equivalent in WGS-84.

Models are frozen and their mappings are copied into read-only views. `GeoURI`
parameter values accepted as string subclasses are stored as built-in strings.
Copies and pickles preserve exact values. `dataclasses.replace` reconstructs a `GeoURI` from
its public float fields and can lose precision; use `build` with Decimal values
instead. `AndroidGeo` is a result container: direct construction stores fields
without validating consistency. Use `parse_android` for validated results.

Android zooms are integers from 1 to 23. Query `+` means a space, while `%2B` means
a literal plus. Empty query values and repeated keys are rejected. Unknown keys
must be UTF-8 encodable, are case-sensitive and retained in `extras`. Pin labels may
contain encoded newlines; they remain labels when parsed. Pin-shaped search text with valid
coordinates is rejected by `build_android_query`; use `build_android` for pins.

## Resource and diagnostic contracts

A numeric token, parsed or built, may contain at most 10,000 characters, including
its sign and decimal point. For nonzero values, coefficient digits plus absolute decimal
exponent must also total at most 10,000. These are resource limits, not RFC rules;
violations raise `GeoURIError` with reason `number`. Other text has no fixed size
limit; memory use grows with input size. Decimal arithmetic context settings do
not change exact comparison or formatting.

Library-generated error messages omit caller data. The reason is the stable
machine-readable interface; diagnostic wording is not a parsing interface.
`GeoURIError(reason, message='')` preserves a caller-provided message verbatim,
including in `args` and pickle state, so callers must avoid putting secrets there.

## Command line and upgrade

`geouri` and `python -m geouri` accept URI arguments or one URI per stdin line.
Only empty lines (after removing CR/LF terminators) are skipped; lines containing
spaces or tabs are rejected with `invalid (scheme)`. Stdin bytes are decoded per
line using the stream encoding. An undecodable line prints `invalid (encoding)`;
valid lines before and after it still produce output. This is a CLI diagnostic,
not an additional `GeoURIError.reason`.
`--json` emits exact JSON numbers and ASCII-escaped strings and keys; `--android` emits JSON
for the Android form. Statuses are 0 for success, 1 for rejected input, and 2 for
invalid options. Mixed batches continue after invalid lines. Diagnostics never
echo rejected inputs or invalid command-line options.

Upgrading from PyPI 0.2.0 keeps valid ordinary parses, builds, comparisons, CLI
success output and model fields. See the dated
[CHANGELOG](https://github.com/JaviLianes8/geouri/blob/main/CHANGELOG.md) for the new
numeric budgets, safer diagnostics, large-zoom fix, undefined comparisons for differing
extension names, and `compare` type checking.
No migration of stored URI text is needed within the documented limits.

## Verification

Install `geouri[dev]` for the development tools. Run `scripts/check.ps1`, supplying
pytest's `--basetemp` through `PYTEST_ADDOPTS` when a dedicated scratch folder is
required. `GEOURI_E2E=1` enables build and installed-wheel tests;
`GEOURI_E2E_PYPI=1` also tests an actual PyPI 0.2.0 installation and upgrade.
Fetch external sources with `python scripts/fetch_upstream.py --output PATH` and
set `GEOURI_UPSTREAM=PATH`. Downloads are checked against the tracked manifest.
Without fetched files only the external-source checks skip.
