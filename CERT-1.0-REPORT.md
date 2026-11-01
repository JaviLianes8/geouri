# geouri 1.0.0 certification report

Date: 2026-11-01. Base: main b56271dd391bc87c38aefc7e3ff3704a2f9426d0.

Progress:
- [x] Certification log checked; release branch created from main
- [x] PyPI 0.2.0 confirmed from the live JSON endpoint
- [x] API, typed errors, runnable docstrings and strict typing reviewed
- [x] RFC and Android reference sources fetched again
- [x] Contracts, seeded properties, README, GUIDE and dated CHANGELOG
- [ ] Wheel, sdist, installed consumer and PyPI upgrade
- [ ] Available interpreter matrix
- [ ] Mutation round, at least ten independent deliberate faults
- [ ] Final four gates and pull request
- [ ] Independent reviewer (item 16)
- [ ] Five independent QA lenses (item 19)
- [ ] Merge and publish (item 17)

## Baseline and API review

PyPI https://pypi.org/pypi/geouri/json reports 0.2.0, fetched 2026-11-01.
Baseline: 250 tests passed, three optional tests skipped; `mypy --strict src tests`
passed. The ten names, function signatures, defaults and model fields remain.
The GUIDE defines the result-container semantics of direct `AndroidGeo`
construction, float-field precision limitations and exact serialization.
`Reason` remains a Literal type alias; its runnable example lives in its defining
module docstring. Every callable public name and `GeoURI.is_wgs84` has examples.

Changes from 0.2.0 are recorded in CHANGELOG: input-free error diagnostics, typed
comparison misuse, numeric resource budgets, safe huge zoom rejection, linear
trailing-zero formatting and removal of the incidental `annotations` attribute.

## Ground truth

Fetched 2026-11-01 into an external scratch folder, selected by `GEOURI_UPSTREAM`.
The tracked `tests/upstream/MANIFEST.json` records URLs, dates, revisions, sizes,
SHA-256 hashes and licences. No downloaded source text is shipped.

- https://www.rfc-editor.org/rfc/rfc5870.txt: SHA-256
  `a3bf93084c422508bbf64976e9adee1eae88d688a2e7f7fc3a531aa44ceb3bb1`.
  The test extracts all sixteen printed URIs and verifies the existing fixture
  against the newly fetched text. Grammar and section 3.4.4 were read directly.
- https://developer.android.com/guide/components/intents-common?hl=en:
  all four Maps examples and the encoded-address example are checked against the
  fetched HTML, including the displayed zoom range of 1 to 23.
- Python's `urllib.parse` is run as an independent oracle for percent encoding,
  decoding and generic URL splitting. `Fraction` checks generated coordinates
  independently of the library's Decimal representation. Generated tests are
  labelled as generated, not as external vectors.

## Validation in progress

The suite includes 6,000 seeded hostile texts through both parsers, 3,000 seeded
coordinate and parameter round trips, 2,000 Android searches checked against
`urllib.parse.quote`, large parameter/query inputs and all public docstrings.
External-source tests skip cleanly when their fetched files are absent.

## Independent review and QA

Items 16 and 19 have not been performed for this release. No lens verdict is
claimed. Merge and publication remain pending.
