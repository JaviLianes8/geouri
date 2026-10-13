# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `GeoURIError.reason`, a closed set of causes exposed as the `Reason` type; errors pickle.
- `compare(a, b)` and RFC 5870 section 3.4.4 equality and hashing on `GeoURI`: exact
  decimal numbers, `wgs84` as the default CRS, poles, date line, parameter order and
  case-insensitive names. `compare` returns `None` where the RFC leaves the result undefined.
- `str(GeoURI)` writes the canonical URI; `GeoURI.is_wgs84`.
- `build(..., params=...)` writes extra parameters with checked names and encoded values,
  and accepts `Decimal` numbers.
- The Android map intent form: `parse_android`, `build_android`, `build_android_query`
  and `AndroidGeo`.
- A `geouri` command (also `python -m geouri`) that prints canonical URIs or JSON.

### Changed

- `parse` follows the RFC 5870 grammar strictly: ASCII digits only, WGS-84 digit limits,
  `crs` then `u` before other parameters and each at most once, no repeated names, label
  names, valid parameter values, no trailing `;`, and clear reasons for a query or fragment.
- Ranges are checked on the exact decimal text and only for WGS-84.
- `build` writes the shortest exact decimal (no more rounding for very small numbers),
  omits `crs=wgs84`, writes longitude 0 at a pole, and refuses booleans and bad labels.
- `GeoURI` validates on construction and its `params` are a read-only mapping.

## [0.1.0]

- First release: `parse` and `build` for geo: URIs (RFC 5870), covering latitude,
  longitude, optional altitude, the `u` uncertainty and `crs` parameters, arbitrary
  extra parameters, and coordinate range validation.
