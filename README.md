# geouri

Typed, zero-dependency parser and builder for geo: URIs (RFC 5870).

## Install

```
pip install geouri
```

## Usage

```python
from geouri import parse, build

location = parse("geo:48.2010,16.3695,183;crs=wgs84;u=23.5")
location.lat  # 48.201
location.lon  # 16.3695
location.alt  # 183.0
location.uncertainty  # 23.5
location.crs  # "wgs84"
location.params  # {}

build(48.2010, 16.3695, alt=183, u=23.5)
# "geo:48.201,16.3695,183;u=23.5"
```

`parse` returns a frozen `GeoURI` with `lat`, `lon`, `alt`, `uncertainty`, `crs` and a
`params` mapping for any extra parameters. It raises `GeoURIError` for a non-`geo:`
scheme, malformed coordinates, a missing value on `crs` or `u`, or a latitude or
longitude outside its range.

`build` writes the shortest valid form, dropping trailing zeros, and validates the
latitude (`[-90, 90]`), longitude (`[-180, 180]`) and uncertainty (non-negative) before
returning.

## Why

RFC 5870 defines the `geo:` URI scheme, but Python has no package for it. The standard
library `urllib.parse` does not model the coordinate path or its parameters, so callers
end up splitting strings by hand and skipping range checks. Rust (`geo-uri`), OCaml and a
thin npm parser cover it elsewhere; this is a small, fully typed take for Python with no
runtime dependencies.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
