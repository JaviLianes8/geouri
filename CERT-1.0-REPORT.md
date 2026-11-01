# geouri 1.0.0 certification report

Date: 2026-11-01. Base: main b56271dd391bc87c38aefc7e3ff3704a2f9426d0.

Progress:
- [x] Certification log checked; release branch created from main
- [x] PyPI 0.2.0 confirmed from the live JSON endpoint
- [x] API, typed errors, runnable docstrings and strict typing reviewed
- [x] RFC and Android reference sources fetched again
- [x] Contracts, seeded properties, README, GUIDE and dated CHANGELOG
- [x] Wheel, sdist, installed consumer and PyPI upgrade
- [x] Available interpreter matrix: twelve builds
- [x] Mutation round: twenty deliberate faults, all caught
- [x] Final four gates and pull request #3
- [x] QA round 1 corrections and contract verification
- [x] QA round 2 corrections and stdin contract verification
- [x] QA round 3 corrections and decoder boundary contracts
- [x] QA round 4 corrections and stdin mutation contracts
- [x] QA round 5 corrections and record multiplicity contracts
- [ ] Independent reviewer (item 16)
- [ ] Five independent QA lenses (item 19)
- [ ] Merge and publish (item 17)

## Scorecard

| Item | Status | Evidence |
| --- | --- | --- |
| 1 | PASS | Existing public names and defaults retained; changes listed in CHANGELOG |
| 2 | PASS | Exact `__all__`, no incidental public imports, examples use public imports |
| 3 | PASS | All ten names have runnable docstrings; README and GUIDE examples executed |
| 4 | PASS | `mypy --strict src tests`; `py.typed` in wheel; consumer type inference tests |
| 5 | PASS | Typed reasons, TypeError for misuse, input-free generated diagnostics |
| 6 | PASS | Every public name covered by success, edge and failure contracts |
| 7 | PASS | Fresh RFC, erratum and Android source checks; Fraction and urllib oracles |
| 8 | PASS | Wheel consumers and CLI, actual PyPI 0.2.0 upgrade, old pickles |
| 9 | PASS | Seeded properties and measured scaling; numeric budgets checked |
| 10 | PASS | Twelve available interpreter builds; installed wheel with source excluded |
| 11 | PASS | Absolute links, scoped comparison, exact badge, strict twine check |
| 12 | PASS | Dated 1.0.0 section: 2026-11-01 |
| 13 | PASS | 1.0.0, Production/Stable, Python 3.10+, MIT, URLs, no runtime dependencies |
| 14 | PASS | Wheel and sdist inspected; LICENSE and typing marker present |
| 15 | PASS | Each gate exits zero; full pytest run: 285 passed, no skips |
| 16 | pending | Independent reviewer |
| 17 | pending | PR #3 open; merge and publication not performed |
| 18 | PASS | Twenty deliberate faults, twenty caught; table below |
| 19 | pending | Five independent QA lenses |

## Baseline and API review

PyPI https://pypi.org/pypi/geouri/json reports 0.2.0, fetched 2026-11-01.
Baseline: 250 tests passed, three optional tests skipped; `mypy --strict src tests`
passed. The ten names, function signatures, defaults and model fields remain.
The GUIDE defines the result-container semantics of direct `AndroidGeo`
construction, float-field precision limitations and exact serialization.
`Reason` remains a Literal type alias with its own runnable docstring. Every
public name and `GeoURI.is_wgs84` has examples.

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
  fetched Maps section, including the displayed zoom range of 1 to 23. The fetch
  script extracts this section before hashing, excluding variable page boilerplate.
- https://www.rfc-editor.org/errata/eid8389: the held erratum confirms the comma
  separators in the two corrected section 6.4 examples. Its HTML is hash-checked.
- Python's `urllib.parse` is run as an independent oracle for percent encoding,
  decoding and generic URL splitting. `Fraction` checks generated coordinates
  independently of the library's Decimal representation. Generated tests are
  labelled as generated, not as external vectors.

## Contract and property validation

The suite includes 6,000 seeded hostile texts through both parsers, 3,000 seeded
coordinate and parameter round trips, 2,000 Android searches checked against
`urllib.parse.quote`, large parameter/query inputs and all public docstrings.
External-source tests skip cleanly when their fetched files are absent.

Measured scaling on 2026-11-01 used five samples at 10,000, 40,000 and 160,000
input units. Fourfold increases took 3.36 to 5.32 times as long for parameter
values, parameter counts, Android queries, near-pin queries and malformed escapes.
Oversized numeric tokens were bounded; no measured ratio exceeded 6.91.
Formatting 2,000/4,000/8,000 trailing zeros 100 times took 0.108/0.222/0.474 seconds.
Rejecting an already-created million-digit integer 1,000 times took 0.033 seconds.

## Packaging and upgrade

The built wheel and sdist pass `twine check --strict`. Archive inspection verifies
MIT LICENSE, `py.typed`, metadata, README, GUIDE, CHANGELOG and the intended tests
and fixtures in the sdist. The wheel contains only the package and distribution
metadata. No caches, downloaded third-party text or process reports ship.

Verified artifact SHA-256:
- wheel: `99dc7c1f69cbe66a9694ee2a34490fa433e9210c9f9910ec5acb158aaeb227a9`
- sdist: `dfc7ef5b1eef380cdc9b620e8f3f537e3157cd87e68310ed557a4c7c79f7ecd5`

Three end-to-end tests passed: fresh wheel installation, an actual PyPI 0.2.0
installation upgraded in place, and archive inspection. Consumers run from empty
folders with isolated Python imports; console and module entry points exercise
canonical text, JSON, Android queries, invalid values and usage errors. Upgrade
checks compare 2,000 generated coordinate records and 2,000 Android searches,
load old exact-value models and error pickles, and verify documented differences
against both installed versions.

## Mutation round (item 18)

Twenty faults were applied individually in an isolated copy of 7ead302.
The final round repeated all twenty after the last runtime changes. The suite ran with
`-x`, a 300-second per-test limit and bytecode disabled; each fault was restored
before the next run. All twenty produced test failures, with no survivors.
Build tests were disabled in this round; the contract suite caught every fault.

| Id | Deliberate mutation | File | Result | Catching test |
| --- | --- | --- | --- | --- |
| M01 | Require lowercase scheme | `_parse.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M02 | Reject latitude 90 | `_validation.py` | killed | `tests/test_build.py::test_pole_longitude_is_written_as_zero` |
| M03 | Reject longitude 180 | `_validation.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M04 | Reject positive instead of negative uncertainty | `_validation.py` | killed | `tests/test_android.py::test_rfc_parameters_and_unknown_fields_are_kept` |
| M05 | Use latitude 91 for the pole rule | `_model.py` | killed | `tests/test_build.py::test_pole_longitude_is_written_as_zero` |
| M06 | Use -181 for the date-line rule | `_model.py` | killed | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| M07 | Return False instead of undefined | `_model.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M08 | Accept misplaced CRS | `_parse.py` | killed | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| M09 | Accept duplicate parameter names | `_parse.py` | killed | `tests/test_certification.py::test_generated_diagnostics_omit_input` |
| M10 | Allow three latitude integer digits | `_grammar.py` | killed | `tests/test_parse.py::test_rejects_with_the_reason` |
| M11 | Raise numeric budget to 100,000 | `_grammar.py` | killed | `tests/test_certification.py::test_numeric_budgets_reject_before_expansion` |
| M12 | Raise ValueError for non-string URI | `_parse.py` | killed | `tests/test_parse.py::test_rejects_a_non_string` |
| M13 | Swap latitude and longitude in build | `_build.py` | killed | `tests/test_android.py::test_builders_write_the_guide_examples` |
| M14 | Limit zoom to 22 instead of 23 | `_android.py` | killed | `tests/test_android.py::test_rfc_parameters_and_unknown_fields_are_kept` |
| M15 | Keep plus instead of decoding space | `_android.py` | killed | `tests/test_android.py::test_address_search_decodes_plus_and_escapes` |
| M16 | Start valid CLI batches with status 1 | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_canonical_form_of_each_argument` |
| M17 | Echo rejected URI in diagnostics | `_cli.py` | killed | `tests/test_certification.py::test_cli_diagnostics_never_echo_inputs_or_unknown_options` |
| M18 | Accept empty parameter values | `_validation.py` | killed | `tests/test_build.py::test_refuses_with_the_reason` |
| M19 | Strip trailing ones as well as zeros | `_grammar.py` | killed | `tests/test_android.py::test_builders_write_the_guide_examples` |
| M20 | Raise ValueError for compare misuse | `_model.py` | killed | `tests/test_certification.py::test_compare_refuses_wrong_types` |

## Available Python matrix

Final wheel from 7ead302, each installed into an isolated environment. Tests come
from the sdist with its source package excluded, so imports resolve to the wheel.
Embedded runtimes were copied into scratch and supplied with isolated dependencies;
original installations were not modified. All three skips are the opt-in build
and upgrade tests, exercised separately in the full run above.

| Python | Installed-wheel suite |
| --- | --- |
| 3.10.11 | 282 passed, 3 skipped |
| 3.10.22 | 282 passed, 3 skipped |
| 3.11.9 | 282 passed, 3 skipped |
| 3.11.11 | 282 passed, 3 skipped |
| 3.11.18 | 282 passed, 3 skipped |
| 3.12.10 | 282 passed, 3 skipped |
| 3.12.16 | 282 passed, 3 skipped |
| 3.13.2 | 282 passed, 3 skipped |
| 3.13.18 | 282 passed, 3 skipped |
| 3.14.6 | 282 passed, 3 skipped |
| 3.14.10t | 282 passed, 3 skipped |
| 3.14.10 | 282 passed, 3 skipped |

Every available minor version from the declared minimum through 3.14 was tested,
including free-threaded 3.14.10. Python 3.13 free-threaded is not installed.
The launcher's stale entries for 3.10.19, 3.11.5/14/17, 3.12.12/15, 3.13.16,
3.14.2/8 and their 3.14 free-threaded builds point to absent executables and could
not run; available replacements are listed above.

## Final gates and pull request

At 7ead302, each command exited zero independently: `ruff format --check .`,
`ruff check .`, `mypy --strict src`, and `pytest`. Strict typing also passed with
`mypy --strict src tests`. With fetched sources, `GEOURI_E2E=1` and
`GEOURI_E2E_PYPI=1`, pytest reported **285 passed, no skips** in 62.43 seconds.
The per-test timeout is 300 seconds. All temporary build and test paths were in
the dedicated scratch directory.

[PR #3](https://github.com/JaviLianes8/geouri/pull/3) targets main from
`release/1.0.0`. The required repository and PR guard returned CLEAN.
Preparation is complete; merge and publication remain pending.

## Independent review and QA

### Round 1 corrections, 2026-11-01

Reviewed base: `33beeadec0e043685bc7961daad98bb693b79575`.
Fix commit: `06f2eb0c40b6ea97c451d51f5101c703307ff513`
(`fix comparison and encoding contracts for 1.0.0`).

The supplied reports for lenses b, c, d and e returned FAIL. All ten reported
findings are addressed below. Independent re-verification remains pending;
this correction run does not replace the lens verdicts or item 16 review.
No verdict for lens a is claimed here. Merge and publication remain pending.

| Finding | Change and verification |
| --- | --- |
| B-01 | `compare` returns `None` for missing, disjoint or partially overlapping extension names when known fields match. Symmetry, boolean inequality and known-field differences are covered; README, GUIDE and docstring corrected. |
| B-02 | Used the report's documentation option to preserve the mapping API. README, GUIDE and parser docstring explicitly restrict repeated extension names, including identical values and flags, and distinguish that restriction from RFC 5870. Four rejection contracts cover the supported subset. |
| C-001 | Decode stdin bytes per line using the stream encoding; emit bounded `invalid (encoding)` and continue with status 1. Six subprocess cases cover malformed, truncated and long invalid UTF-8 lines between valid records, in both modes. |
| C-002 | Reject unpaired surrogate query keys with `GeoURIError` reason `query`. Three parser contracts and a strict UTF-8 CLI output contract verify rejection and bounded diagnostics. |
| C-003 | Store accepted parameter string subclasses as built-in strings through the base implementation. The contract checks exact content, serialization, equality and hash consistency despite a subclass display override. |
| D-001 | Serialize JSON strings and keys with ASCII escapes while retaining exact Decimal numbers. Subprocess checks cover ASCII/cp1252, Unicode keys and values, both CLI entry points and both JSON modes after wheel and sdist installation. |
| E-01 | Assert complete `GeoURIError.args` with default, nonempty and newline messages before and after pickling. |
| E-02 | Assert non-default CRS, exact canonical text, equality and hash preservation through pickle, shallow copy and deep copy, using coordinates outside WGS-84 ranges. |
| E-03 | Assert pin, label and query separately for newline, CRLF and newline-only label round trips, plus a directly parsed percent-encoded newline. |
| E-04 | Document that empty lines are skipped while whitespace-only lines are rejected; subprocess contract checks spaces, tabs, status, diagnostics and continued valid output. |

The new contracts ran against unchanged source before behavior fixes: **18 failed,
13 passed**, with failures for all five behavior defects. After correction all
**31 passed**. B-02 and E-01 through E-04 preserve current runtime behavior.
Two prior comparison cases asserting `False` for differing unknown names were
replaced by the stronger undefined-comparison contracts.

The four previously surviving mutations were replayed individually in scratch
copies. Each produced assertion failures, with no collection errors or timeouts:

| Finding | Mutation | Catching contract |
| --- | --- | --- |
| E-01 | Drop message from exception constructor args | `test_error_args_preserve_the_complete_message_through_pickle` |
| E-02 | Replace serialized CRS with default | `test_non_default_crs_survives_pickle_and_copies` |
| E-03 | Remove DOTALL from pin matching | `test_android_newline_labels_remain_pins` |
| E-04 | Skip whitespace-only stdin | `test_whitespace_only_stdin_is_rejected_while_empty_lines_are_skipped` |

Each required gate exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and pytest. Strict typing also passed for `src tests`.
The complete suite reported **314 passed, no skips** in 90.62 seconds on
CPython 3.14.6, with fetched upstream references, `GEOURI_E2E=1` and
`GEOURI_E2E_PYPI=1`. This includes a fresh wheel, an sdist installation and an
actual PyPI 0.2.0 upgrade. Every pytest run used a 300-second per-test timeout
and a dedicated scratch basetemp. No interpreter matrix was repeated this round.

Local evidence is under `C:/lianes8-build/codex-pylib/scratch/geouri-cert/fix-r1/`:
`red-corrected.txt`, `full.xml`, and `mutation-E-01` through `mutation-E-04`
containing the replay outputs and JUnit results. All runtime changes and the
documentation restriction are recorded in CHANGELOG.

### Round 2 corrections, 2026-11-01

Reviewed base: `db00ec81ece31b2bd0cc0eeabebaf71af9caa846`.
Fix commit: `acf7da7522d18255b7a6db5899850ed1f312146d`
(`preserve stdin decoder state and universal newlines`).

All four supplied findings are addressed. B-03, C-004 and D-002 describe the
same stdin framing regression; E-05 identifies a missing encoding contract.
Independent lens re-verification and item 16 review remain pending. No new
lens verdict, merge or publication is claimed by this correction run.

| Finding | Change and verification |
| --- | --- |
| B-03 | Decode the entire batch with one incremental text reader before splitting records. Contracts cover CR, LF and CRLF, UTF-16 LE/BE and BOM, UTF-32 LE and BOM, empty lines and an unterminated final record. |
| C-004 | Retain bounded per-record encoding diagnostics and valid neighboring records. Nine cases combine malformed UTF-8/UTF-16/UTF-32 with all three newline forms; existing malformed UTF-8 contracts also pass. Additional checks cover incomplete final code units, valid replacement characters and a UTF-7 shift spanning newlines. |
| D-002 | Installed wheel and sdist consumers exercise both module and console entry points with CR/LF/CRLF batches in UTF-8, UTF-16 LE/BOM, UTF-32 LE and cp1252. Every record, decoded query, status and empty stderr are asserted. |
| E-05 | A subprocess supplies non-ASCII cp1252 stdin with valid neighboring records and asserts all decoded queries, successful status and empty stderr. It kills the exact N15 mutation on the reviewed source and the equivalent mutation in the revised reader. |

Before the runtime correction, the expanded encoding contract file reported
**21 failed, 20 passed**. These failures reproduce the shared behavior bug and
its malformed-record variants. The cp1252 contract passed on the original source,
as expected for a coverage finding. After the fix, both CLI test files reported
**51 passed**. Four additional finalization and stateful-decoding cases were then
included in the complete suite. The public API is unchanged; GUIDE describes
incremental decoding and universal newlines, and CHANGELOG records the behavior
restoration and added contracts.

| Mutation replay | Result | Catching contract |
| --- | --- | --- |
| N15: replace `stream.encoding` with UTF-8 in the original reader | Killed by an assertion failure | `test_stdin_uses_the_configured_cp1252_codec` |
| N15 equivalent: force UTF-8 in the revised text reader | Killed by an assertion failure | `test_stdin_uses_the_configured_cp1252_codec` |

Each required gate exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and pytest. Strict typing also passed for `src tests`.
The full suite reported **347 passed, no skips** in 74.00 seconds on CPython
3.14.6 with manifest-checked upstream references, `GEOURI_E2E=1` and
`GEOURI_E2E_PYPI=1`. It built and installed the wheel and sdist and exercised an
actual PyPI 0.2.0 upgrade. Every pytest run used a 300-second per-test timeout
and a scratch basetemp. No interpreter matrix was repeated this round.

Local evidence is under `C:/lianes8-build/codex-pylib/scratch/geouri-cert/fix-r2/`:
`red.txt`, `red.xml`, `green.xml`, `full.txt`, `full.xml`, and `N15-original/`
and `N15-fixed/`, each containing mutation output and JUnit results.

### Round 3 corrections, 2026-11-01

Reviewed base: `9026b143ee1d8e35ee04a9a7ea498960934dc3b4`.
Fix commit: `5c7e869ebce832dbbcf64492a3174d2be9329380`
(`fix unrecoverable stdin decoding and strengthen contracts`).

All five supplied findings are addressed. B-04, C-005 and D-003 describe the
same unrecoverable decoder failure; E-06 and E-07 identify missing contracts.
Independent lens re-verification and item 16 review remain pending. No new
lens verdict, merge or publication is claimed by this correction run.

| Finding | Change and verification |
| --- | --- |
| B-04 | Catch `UnicodeDecodeError` escaping stdin iteration, emit one bounded `invalid (encoding)` diagnostic and stop safely with status 1. Eighteen subprocess cases cover UTF-16/UTF-32 missing or damaged BOMs and ASCII prefixes in canonical, JSON and Android modes. |
| C-005 | Retain recoverable-record handling while stopping when decoder state cannot resume. Contracts assert empty stdout and the exact diagnostic, and verify caller-owned handles remain open and reusable after both recoverable and unrecoverable errors. |
| D-003 | Wheel and sdist consumers exercise missing/damaged BOM and ASCII-prefix rejection through both module and console entry points, asserting status 1, empty stdout and the exact encoding diagnostic. |
| E-06 | A caller-owned TextIOWrapper over BytesIO remains open after success or either decoding failure. Contracts rewind and read the original bytes, then rewrite and read through the same text stream. They kill R09. |
| E-07 | Source and installed-distribution subprocesses supply byte 0x80 under cp1252 and assert query U+20AC, status 0 and empty stderr. These contracts kill R18 in source, wheel and sdist tests. The previous cp1252 accented-text contract still kills forced UTF-8 decoding. |

Before the runtime correction, the new contract file reported **19 failed,
3 passed**, reproducing the decoder failure while preserving the successful
ownership and codec-identity cases. After correction, all three CLI contract
files reported **77 passed**. The public API remains unchanged. README and GUIDE
describe unrecoverable batch termination, and CHANGELOG records the behavior
change and added contracts.

Mutations were applied individually in scratch copies and restored afterward.
Each failure below was an assertion failure, with no collection errors or timeouts.

| Mutation replay | Result | Catching contract |
| --- | --- | --- |
| R09: replace `reader.detach()` with `reader.close()` | Killed: three failed cases | `test_stdin_remains_open_and_reusable_by_caller` |
| R18: replace cp1252 decoding with Latin-1 | Killed: source, installed wheel and installed sdist assertions | `test_cp1252_stdin_preserves_euro_query` and installed `_check_cp1252_euro` |
| E-05 replay: force UTF-8 decoding | Killed: one failed case | `test_stdin_uses_the_configured_cp1252_codec` |

Each required gate exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and pytest. Strict typing also passed for `src tests`.
The complete suite reported **369 passed, no skips** in 110.66 seconds on CPython
3.14.6 with manifest-checked upstream references, `GEOURI_E2E=1` and
`GEOURI_E2E_PYPI=1`. It built and installed the wheel and sdist, checked both CLI
entry points, and exercised an actual PyPI 0.2.0 upgrade. Every pytest run used
a 300-second per-test timeout and a scratch basetemp. No interpreter matrix was
repeated this round.

Local evidence is under `C:/lianes8-build/codex-pylib/scratch/geouri-cert/fix-r3/`:
`red.txt`, `red.xml`, `green.xml`, `full-3.txt`, `full.xml`, `full-gates.json`,
and `mutations.json`. The `R09/`, `R18/` and `E05/` directories contain the
individual mutation output and JUnit results.

### Round 4 corrections, 2026-11-01

Reviewed base: `74ee527044f2180d36524715f28f1691fffc602c`.
Fix commit: `2c916c4540035867df3746f4da2c6b170ed0f915`
(`strengthen stdin decoding and case preservation contracts`).

E-08, E-09 and E-10 identify missing contracts, with no production defect in the
reviewed implementation. Twelve new source cases pass on that implementation.
The runtime and public API remain unchanged; CHANGELOG records the added coverage.
Independent lens re-verification and item 16 review remain pending.

| Finding | Change and verification |
| --- | --- |
| E-08 | UTF-16 and UTF-32 input without a BOM spans multiple decoder buffers (32 and 64 KiB). Six source cases cover canonical, JSON and Android output, requiring status 1, empty stdout and exactly one encoding diagnostic. Installed wheel and sdist consumers enforce the same termination contract. |
| E-09 | Invalid UTF-8 bytes occur at the beginning, middle and end of query data after a valid URI prefix. Source and installed contracts require the exact encoding diagnostic, status 1 and both neighboring valid records in order. |
| E-10 | UTF-8, cp1252 and UTF-16 stdin must preserve `Main Street`, `Town Hall` and `Blue` as query, label and parameter values, with successful status and empty stderr. Source and installed contracts assert exact case. |

Installed checks exercise both module and console entry points from an empty
working directory with the source path excluded. All inputs added this round
are hand-written contract cases.

The exact N06, N11 and N20 patches were replayed individually in scratch copies.
Each caused assertion failures in the new source contracts and in both installed
distribution tests, with no collection errors or timeouts. The live upgrade was
disabled for mutation runs; it passed in the full unmodified run.

| Mutation replay | Source result and catching contract | Installed result |
| --- | --- | --- |
| N06: resume an unrecoverable decoder | Six failures in `test_unrecoverable_large_batch_stops_after_one_diagnostic` | Wheel and sdist fail `_check_large_bom_error` |
| N11: detect invalid bytes only at the record start | Three failures in `test_embedded_decode_error_keeps_encoding_diagnostic` | Wheel and sdist fail `_check_embedded_decode_error` |
| N20: lowercase decoded records | Three failures in `test_stdin_preserves_query_case` | Wheel and sdist fail `_check_query_case` |

All 34 tests in `test_stdin_contracts.py` passed on the unchanged implementation.
Each required gate exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and pytest. Strict typing also passed for `src tests`.
The complete suite reported **381 passed, no skips** in 173.63 seconds on CPython
3.14.6 with freshly fetched, manifest-checked upstream references, `GEOURI_E2E=1`
and `GEOURI_E2E_PYPI=1`. This includes wheel and sdist installation, both CLI entry
points and an actual PyPI 0.2.0 upgrade. Every pytest run used a 300-second
per-test timeout and a scratch basetemp. No interpreter matrix was repeated.

Local evidence is under `C:/lianes8-build/codex-pylib/scratch/geouri-cert/fix-r4/`:
`baseline.txt`, `baseline.xml`, `full-4.txt`, `full.xml`, `full-gates.json`,
`mutations.json`, and the `N06`, `N11` and `N20` source/installed text and JUnit
logs. The mutation source copies were restored after verification.

### Round 5 corrections, 2026-11-01

Reviewed base: `fee943e841f4ee58dda7c4165f25dcb3e2eaedfe`.
Fix commit: `fb8dfed7faf09e49b475a4e3c611c03c81abbcc2`
(`strengthen stdin multiplicity and whitespace contracts`).

E-11, E-12 and E-13 identify missing contracts, with no production defect in the
reviewed implementation. Nine new source cases pass on that implementation.
The runtime and public API remain unchanged; CHANGELOG records the added coverage.
Independent lens re-verification and item 16 review remain pending.

| Finding | Change and verification |
| --- | --- |
| E-11 | Canonical, JSON and Android modes must retain consecutive and nonconsecutive duplicate records. Source and installed contracts assert the exact five-record output sequence, including distinct neighboring records. |
| E-12 | Three malformed records interleaved with valid records must emit exactly three encoding diagnostics and preserve the valid output sequence. A record containing two invalid bytes still produces one diagnostic. All three output modes are covered. |
| E-13 | Android queries preserve literal tabs, repeated tabs, and leading and trailing spaces or tabs. Source and installed contracts assert the exact query text, output count, successful status and empty stderr. |

Installed checks exercise both module and console entry points after wheel and
sdist installation, from empty consumer directories with the source path excluded.
All inputs added this round are hand-written contract cases.

The exact R05, R06 and R10 patches were replayed individually in scratch copies.
Each caused assertion failures in the new source contracts and in both installed
distribution tests, with no collection errors or timeouts. The live upgrade was
disabled for mutation runs; it passed in the full unmodified run.

| Mutation replay | Source result and catching contract | Installed result |
| --- | --- | --- |
| R05: skip consecutive identical records | Three failures in `test_duplicate_stdin_records_preserve_count_and_order` | Wheel and sdist fail the exact record sequence assertion in `check_records` |
| R06: report only the first recoverable decoding error | Three failures in `test_each_malformed_stdin_record_has_one_diagnostic` | Wheel and sdist fail the diagnostic count assertion in `check_records` |
| R10: replace tabs with spaces | Three failures in `test_stdin_preserves_query_whitespace` | Wheel and sdist fail the exact query assertion in `check_records` |

All 43 tests in `test_stdin_contracts.py` passed on the unchanged implementation.
Each required gate exited 0: `ruff format --check .`, `ruff check .`,
`mypy --strict src`, and pytest. Strict typing also passed for `src tests`.
The complete suite reported **390 passed, no skips** in 115.04 seconds on CPython
3.14.6 with manifest-checked upstream references, `GEOURI_E2E=1` and
`GEOURI_E2E_PYPI=1`. This includes wheel and sdist installation, both CLI entry
points and an actual PyPI 0.2.0 upgrade. Every pytest run used a 300-second
per-test timeout and a scratch basetemp. No interpreter matrix was repeated.

Local evidence is under `C:/lianes8-build/codex-pylib/scratch/geouri-cert/fix-r5/`:
`baseline.txt`, `baseline.xml`, `full-4.txt`, `full.xml`, `full-gates.json`,
`mutations.json`, and the `R05`, `R06` and `R10` source/installed text and JUnit
logs. The mutation source copies were restored after verification.

### Disputed findings

None.
