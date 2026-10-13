# geouri improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: RFC 5870 examples and errata, Android map intent examples
- [x] Error reasons: `GeoURIError.reason` from a closed set, picklable
- [x] Strict RFC 5870 parser: grammar, WGS-84 digit limits, parameter order and duplicates
- [x] Exact numbers: ranges and comparison on the decimal text, not on rounded floats
- [x] Comparison per section 3.4.4: poles, date line, crs default, unknown parameters
- [x] Safe builder: shortest exact numbers, encoded parameters, refused labels
- [x] Android dialect: `parse_android`, `build_android`, `build_android_query`
- [x] Command line: canonical form or JSON per URI, Android mode
- [ ] Contracts: RFC examples, README examples, typing, installed wheel
- [x] Docs and packaging: README, CHANGELOG, metadata, sdist contents
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Mutation run: removing guarded logic makes the suite fail
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `parse`, `build`, a frozen `GeoURI` and `GeoURIError`. Checked against the
sources below:

- `\d` in the number pattern matches any Unicode digit, so `geo:٤٨,16` parses as latitude
  48. The grammar only allows ASCII `DIGIT`.
- Ranges are checked on the float, so `geo:90.0000000000000000001,0` is accepted: the text
  rounds to `90.0` before the check. Section 3.4.2 says such a URI is invalid.
- WGS-84 restricts latitude to `1*2DIGIT` and longitude to `1*3DIGIT` before the point;
  `geo:090,0` is accepted.
- `crs` and `u` may appear in any order and any number of times (the last one wins), and
  may follow other parameters. Section 3.3 forbids all three.
- Parameter names and values are not checked against `labeltext` and `paramchar`:
  `geo:1,2;a b=c d`, `geo:1,2;x=` and `geo:1,2;x=%zz` all parse.
- A query or fragment (`geo:1,2?z=3`) fails with a confusing "invalid longitude" message.
- Ranges are applied to every CRS, although section 3.4.1 only defines them for WGS-84.
- Equality is the dataclass field comparison: the poles rule, the date line rule and exact
  decimal comparison from section 3.4.4 are missing, and `GeoURI` is not hashable because
  `params` is a plain dict that can be changed in place.
- `build` writes numbers through `f"{x:.12f}"` when `repr` uses an exponent, so
  `build(1.234567891234e-5, 0)` loses digits. It writes any `crs` text and has no way to add
  other parameters safely.
- Every error is a bare `GeoURIError` with prose; callers cannot branch on the cause.
- The Android `geo:` intent form (`?z=`, `?q=`) used by most map apps is not supported.

## Sources (fetched 2026-10-13)

- RFC 5870, https://www.rfc-editor.org/rfc/rfc5870.txt (sha256
  a3bf93084c422508bbf64976e9adee1eae88d688a2e7f7fc3a531aa44ceb3bb1): ABNF (3.3), CRS
  (3.4.1), WGS-84 components and ranges (3.4.2), uncertainty (3.4.3), comparison (3.4.4),
  encoding (3.5), examples (6), comparison examples (6.4), invalid locations (9.1).
- RFC 5870 errata, https://www.rfc-editor.org/errata/rfc5870: 7232 (verified, editorial
  wording only) and 8389 (held for document update): the first comparison example in
  section 6.4 uses `;` where `,` was meant between latitude and longitude.
- IANA registry, https://www.iana.org/assignments/geo-uri-parameters/: only `crs` and `u`
  are registered; the only `crs` value is `wgs84`.
- Android common intents, https://developer.android.com/guide/components/intents-common
  (section Maps): `geo:lat,lng`, `?z=` zoom from 1 to 23, `geo:0,0?q=lat,lng(label)` and
  `geo:0,0?q=address` with `+` or `%20` for spaces.

## Ranked improvements

1. Closed set of error reasons on `GeoURIError` (`reason` attribute, `Literal` type,
   picklable), so callers and the command line can report the cause.
2. Strict parser that follows the ABNF exactly: ASCII digits, WGS-84 digit limits,
   `labeltext` names, `paramchar` values with valid percent-encoding and UTF-8, no empty
   value, `crs` first, `u` second, each at most once, no duplicate names, a clear reason for
   a query or fragment.
3. Exact numbers: keep the decimal text of every coordinate, check ranges on it, and print
   it back without rounding.
4. Comparison per section 3.4.4: same CRS with `wgs84` as default, mathematically identical
   numbers, longitude ignored at the poles, 180 equal to -180, parameter order ignored,
   unknown parameters equal only when names match and decoded values are identical.
   `compare(a, b)` returns `None` where the RFC calls the result undefined; `==` and `hash`
   agree with it.
5. Ranges only for WGS-84; other CRS labels parse syntactically and are exposed as is.
6. Safe builder: shortest exact decimal form, `Decimal` input accepted, `bool` and
   non-finite numbers refused, `crs` checked against `labeltext`, extra parameters with
   checked names and percent-encoded values, longitude written as 0 at a pole (section
   3.4.2 SHOULD).
7. `str(GeoURI)` gives the canonical form; `params` becomes a read-only mapping and the
   model is hashable.
8. Android dialect, documented as non-RFC: `parse_android` returns the point, zoom, search
   text, pin and label; `build_android` and `build_android_query` write it.
9. Command line `geouri`: canonical form or JSON per URI, from arguments or stdin, exit 1
   with the reason for invalid input, `--android` for the intent form.
10. Contracts: RFC examples copied by script into `tests/data`, a check against the fetched
    RFC text (skipped while absent, see `scripts/fetch_upstream.py`), README examples run,
    mypy reveals the documented types, installed wheel driven end to end.
11. Docs and packaging: README with an API table and the reasons list, CHANGELOG `0.2.0`,
    keywords and classifiers, sdist limited to sources and tests.

Deferred: GML mapping from section 7 (non-normative, would pull XML into a small parser);
other CRS labels (none registered).
