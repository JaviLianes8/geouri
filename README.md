# geouri

Strict, typed, zero-dependency parser, builder and comparator for `geo:` URIs
([RFC 5870](https://www.rfc-editor.org/rfc/rfc5870)), plus the Android map intent form
(`?z=` zoom, `?q=` search) that most map apps accept.

## Install

```
pip install geouri
```

## Usage

### Parse

```python
from geouri import parse

uri = parse("geo:48.198634,16.371648;crs=wgs84;u=40")
print(uri.lat, uri.lon)  # 48.198634 16.371648
print(uri.alt, uri.uncertainty, uri.crs)  # None 40.0 wgs84
print(uri)  # geo:48.198634,16.371648;u=40

uri = parse("GEO:66.0,30,183;U=6.500;Type=this%2dthat;flag")
print(uri.alt, uri.uncertainty)  # 183.0 6.5
print(dict(uri.params))  # {'type': 'this-that', 'flag': None}
print(uri)  # geo:66,30,183;u=6.5;type=this-that;flag
```

`parse` follows the grammar of section 3.3: ASCII digits only, at most two
integer digits of latitude and three of longitude in WGS-84, `crs` first and `u` second,
each at most once, parameter names made of letters, digits and `-`, values made of the
allowed characters or valid percent-encoding. One deliberate tightening: decoded values
must be UTF-8, since they are returned as `str`. Ranges are checked on the exact decimal
text, so `geo:90.0000000000000000001,0` is refused even though it rounds to `90.0` as a
float. Other CRS labels parse, but their coordinates are not range checked because RFC 5870
only defines WGS-84.

### Errors

```python
from geouri import GeoURIError, parse


def reason(text: str) -> str:
    try:
        parse(text)
    except GeoURIError as error:
        return error.reason
    return "valid"


print(reason("geo:94,0"))  # latitude-range
print(reason("geo:1,2;u=5;crs=wgs84"))  # param-order
print(reason("geo:1,2?z=11"))  # query
print(reason("geo:1,2;x=a b"))  # param-value
```

Each `GeoURIError` (a `ValueError`) carries a `reason` from the closed set listed under
[Reasons](#reasons).

### Build

```python
from decimal import Decimal

from geouri import build

print(build(48.2010, 16.3695, alt=183, u=23.5))  # geo:48.201,16.3695,183;u=23.5
print(build(1.234567891234e-5, 0))  # geo:0.00001234567891234,0
print(build(Decimal("0.10000000000000000001"), 180))  # geo:0.10000000000000000001,180
print(build(90, 123))  # geo:90,0
params = {"name": "Café & bar", "x": None}
print(build(1, 2, crs="WGS84", params=params))  # geo:1,2;name=Caf%C3%A9%20&%20bar;x
```

`build` validates everything `parse` checks, writes each number in its shortest exact
decimal form (a float reads back as the same float, a `Decimal` keeps its digits), writes
longitude 0 at a pole as section 3.4.2 recommends, writes the date line as 180 so equal
URIs print the same text, leaves out the default `crs`, and
percent-encodes parameter values. Booleans, strings and non-finite numbers are refused.

### Compare

```python
from geouri import compare, parse

print(parse("geo:90,-22.43;crs=WGS84") == parse("geo:90,46"))  # True
print(parse("geo:10,180") == parse("geo:10,-180"))  # True
print(parse("geo:47,11;a=1;b=2") == parse("geo:47,11;b=2;a=1"))  # True
print(parse("geo:1,2") == parse("geo:1,2,0"))  # False
print(compare(parse("geo:22,0;bar=Blue"), parse("geo:22,0;BAR=blue")))  # None
```

`==` and `hash` follow section 3.4.4: same CRS (missing means `wgs84`), numbers compared
as exact decimals, longitude ignored at the poles and 180 equal to -180 in WGS-84,
parameter order ignored, names case-insensitive and values compared after
percent-decoding. `compare` returns `None` where the RFC calls the result undefined: the
same unknown parameters appear but some values differ, which only the parameter's own
specification could settle. `==` treats that case as not equal.

### Android map intents

```python
from geouri import build_android, build_android_query, parse_android

geo = parse_android("geo:47.6,-122.3?z=11")
print(geo.point, geo.zoom)  # geo:47.6,-122.3 11
geo = parse_android("geo:0,0?q=34.99,-106.61(Treasure)")
print(geo.pin, geo.label)  # geo:34.99,-106.61 Treasure
geo = parse_android("geo:0,0?q=1600+Amphitheatre+Parkway%2C+CA")
print(geo.query)  # 1600 Amphitheatre Parkway, CA
print(build_android(34.99, -106.61, label="Treasure"))  # geo:0,0?q=34.99,-106.61(Treasure)
print(build_android_query("1st & Pike", zoom=15))  # geo:0,0?q=1st%20%26%20Pike&z=15
```

This form is not part of RFC 5870, so `parse` refuses it with reason `query`. It follows
the Maps section of the
[Android common intents guide](https://developer.android.com/guide/components/intents-common):
the part before `?` is an RFC 5870 point, `z` is a zoom from 1 to 23, and `q` is either
`lat,lng(label)` or free search text, with `+` or `%20` for spaces. Other query fields are
kept in `extras`. Pin-shaped `q` text whose coordinates are out of range is read as search
text, and `build_android_query` refuses text that a map app would read as a pin.

### Command line

```
geouri "geo:48.2010,16.3695;CRS=WGS84;U=40" "geo:94,0"
geo:48.201,16.3695;u=40
invalid (latitude-range): geo:94,0
```

Prints the canonical form of each URI, or reads one per line from standard input when none
are given. `--json` prints the fields as JSON, `--android` reads the Android form and
prints JSON. JSON numbers are the exact decimals of the URI. The exit status is 1 if any URI is invalid and 2 for a usage error.

## API

| Name | What it does |
| --- | --- |
| `parse(uri)` | Parse an RFC 5870 URI into a `GeoURI`, or raise `GeoURIError`. |
| `build(lat, lon, *, alt, u, crs, params)` | Validate the parts and return the canonical URI text. |
| `compare(a, b)` | Section 3.4.4 comparison: `True`, `False`, or `None` when undefined. |
| `GeoURI` | Frozen, hashable model: `lat`, `lon`, `alt`, `uncertainty`, `crs`, read-only `params`, `is_wgs84`; `str()` is canonical. |
| `GeoURIError` | `ValueError` with a `reason` and a `message`; survives pickling. |
| `Reason` | The `Literal` type of every reason. |
| `parse_android(uri)` | Parse the Android map intent form into an `AndroidGeo`. |
| `build_android(lat, lon, *, zoom, label)` | Write `geo:lat,lng?z=` or `geo:0,0?q=lat,lng(label)`. |
| `build_android_query(query, *, zoom)` | Write `geo:0,0?q=` with encoded search text. |
| `AndroidGeo` | Frozen result: `point`, `zoom`, `query`, `pin`, `label`, `extras`. |

### Reasons

- `scheme`: not a `geo:` URI.
- `coordinates`: not two or three comma-separated coordinates.
- `number`: a coordinate that is not a plain decimal, or too many integer digits in WGS-84.
- `latitude-range`: WGS-84 latitude outside [-90, 90].
- `longitude-range`: WGS-84 longitude outside [-180, 180].
- `uncertainty`: `u` missing its value, not a plain decimal, or negative.
- `crs`: `crs` missing its value or not a label.
- `param-name`: an empty segment, a name that is not a label, or `crs`/`u` among extras.
- `param-value`: an empty value, a character that must be encoded, bad percent-encoding or UTF-8.
- `duplicate-param`: a parameter given twice (names are case-insensitive).
- `param-order`: `crs` not first, or `u` after another parameter.
- `query`: a `?` in an RFC 5870 URI, or a malformed Android query.
- `fragment`: a `#` anywhere.
- `zoom`: an Android zoom that is not a whole number from 1 to 23.

## Why

RFC 5870 defines the `geo:` URI scheme, but Python has no package that follows it closely.
`urllib.parse` does not model the coordinates or parameters, so callers split strings by
hand, skip range checks, compare floats where the RFC compares decimals, and miss the poles
and date line rules. This package does the whole job with no runtime dependencies, full
type hints, and tests that pin every example printed in the RFC.

## Development

`scripts/check.ps1` runs the gate (format, lint, `mypy --strict`, tests).
`python scripts/fetch_upstream.py` fetches the RFC text listed in
`tests/upstream/MANIFEST.json`, so the test that checks the committed examples against it
runs instead of skipping. `GEOURI_E2E=1` builds the wheel, installs it in a fresh virtual
environment and drives it.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
