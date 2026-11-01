# geouri 1.0.0 certification report

Date: 2026-11-01. Base: main b56271dd391bc87c38aefc7e3ff3704a2f9426d0.

Progress:
- [x] Certification log checked; release branch created from main
- [x] PyPI 0.2.0 confirmed from the live JSON endpoint
- [x] API, typed errors, runnable docstrings and strict typing reviewed
- [x] RFC and Android reference sources fetched again
- [x] Contracts, seeded properties, README, GUIDE and dated CHANGELOG
- [x] Wheel, sdist, installed consumer and PyPI upgrade
- [ ] Available interpreter matrix
- [x] Mutation round: twenty deliberate faults, all caught
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

## Packaging and upgrade

The built wheel and sdist pass `twine check --strict`. Archive inspection verifies
MIT LICENSE, `py.typed`, metadata, README, GUIDE, CHANGELOG and the intended tests
and fixtures in the sdist. The wheel contains only the package and distribution
metadata. No caches, downloaded third-party text or process reports ship.

Three end-to-end tests passed: fresh wheel installation, an actual PyPI 0.2.0
installation upgraded in place, and archive inspection. Consumers run from empty
folders with isolated Python imports; console and module entry points exercise
canonical text, JSON, Android queries, invalid values and usage errors. Upgrade
checks compare 2,000 generated coordinate records and 2,000 Android searches,
load old exact-value models and error pickles, and verify documented differences
against both installed versions.

## Mutation round (item 18)

Twenty faults were applied individually in an isolated copy. The suite ran with
`-x`, a 300-second per-test limit and bytecode disabled; each fault was restored
before the next run. All twenty produced assertion failures, with no survivors.
Build tests were disabled in this round; the contract suite caught every fault.

| Id | Deliberate mutation | File | Result | Catching test |
| --- | --- | --- | --- | --- |
| M01 | scheme case | `_parse.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M02 | latitude upper boundary | `_validation.py` | killed | `tests/test_build.py::test_pole_longitude_is_written_as_zero` |
| M03 | longitude upper boundary | `_validation.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M04 | negative uncertainty | `_validation.py` | killed | `tests/test_android.py::test_rfc_parameters_and_unknown_fields_are_kept` |
| M05 | pole equivalence | `_model.py` | killed | `tests/test_build.py::test_pole_longitude_is_written_as_zero` |
| M06 | date line equivalence | `_model.py` | killed | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| M07 | unknown values comparison | `_model.py` | killed | `tests/test_certification.py::test_public_docstrings_and_guide_examples_run` |
| M08 | parameter order | `_parse.py` | killed | `tests/test_docs.py::test_every_readme_example_runs_and_prints_its_comment` |
| M09 | duplicate parameters | `_parse.py` | killed | `tests/test_certification.py::test_generated_diagnostics_omit_input` |
| M10 | latitude digit width | `_grammar.py` | killed | `tests/test_parse.py::test_rejects_with_the_reason` |
| M11 | number budget | `_grammar.py` | killed | `tests/test_certification.py::test_numeric_budgets_reject_before_expansion` |
| M12 | wrong error type | `_parse.py` | killed | `tests/test_parse.py::test_rejects_a_non_string` |
| M13 | swapped build arguments | `_build.py` | killed | `tests/test_android.py::test_builders_write_the_guide_examples` |
| M14 | Android upper zoom | `_android.py` | killed | `tests/test_android.py::test_rfc_parameters_and_unknown_fields_are_kept` |
| M15 | Android plus decoding | `_android.py` | killed | `tests/test_android.py::test_address_search_decodes_plus_and_escapes` |
| M16 | CLI success status | `_cli.py` | killed | `tests/test_cli.py::test_prints_the_canonical_form_of_each_argument` |
| M17 | CLI privacy | `_cli.py` | killed | `tests/test_certification.py::test_cli_diagnostics_never_echo_inputs_or_unknown_options` |
| M18 | empty parameter value | `_validation.py` | killed | `tests/test_build.py::test_refuses_with_the_reason` |
| M19 | exact number formatting | `_grammar.py` | killed | `tests/test_android.py::test_builders_write_the_guide_examples` |
| M20 | type comparison check | `_model.py` | killed | `tests/test_certification.py::test_compare_refuses_wrong_types` |

## Independent review and QA

Items 16 and 19 have not been performed for this release. No lens verdict is
claimed. Merge and publication remain pending.
