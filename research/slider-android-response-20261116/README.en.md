# Android Slider G-response capture archive · 2026-11-16

This directory archives four completed Android acquisition rounds and explicitly labelled subsequent post-acquisition diagnostics, with no new acquisition or parameter tuning. **Successful acquisition does not establish visual, interaction or optical acceptance.** See the original [PLAN.md](PLAN.md) and pre-acquisition identity manifest [FREEZE.json](FREEZE.json).

## Preserved acquisition

The four receipts, results and indexes were read directly. Each instrumentation run records `exit_code=0` and `test_passed=true`; each result is `passed`, and each frozen indexer result is `original_hashes_pointer_and_pair_checks_passed`. Each round contains six poses × shape/flat: **12 held endpoints and 49 original files** (48 PNGs plus one `result.json`). Every receipt file records a matching device/host hash.

| Order | Condition | Held endpoints | Original files | Original receipt |
| --- | --- | ---: | ---: | --- |
| 1 | control-pre | 12 | 49 | [receipt.json](evidence/rounds/control-pre/android-r2/receipt.json) |
| 2 | global-G | 12 | 49 | [receipt.json](evidence/rounds/global-G/android-r2/receipt.json) |
| 3 | mask-G | 12 | 49 | [receipt.json](evidence/rounds/mask-G/android-r2/receipt.json) |
| 4 | control-post | 12 | 49 | [receipt.json](evidence/rounds/control-post/android-r2/receipt.json) |

Total: 48 held endpoints and 196 original files. All four receipts bind the same `FREEZE.json`, SHA-256 `4cd995935db016027d5c37cb472b53c7ea205a063aa7dc68412a265e2f704e23`. These records establish acquisition integrity, not agreement between systems' responses.

## Analysis status and repository boundary

The pre-acquisition-frozen [analyze.py](analyze.py) passed 19 pure mathematics/gate self-tests, but failed while loading the first real round: it assumed an absent `source_manifest` field and a copied manifest location. Further checks found index identity and geometry field-name differences. The frozen file remains unchanged.

[analyze-compatible.py](analyze-compatible.py) is a **post-acquisition I/O/schema repair**. It reads the bound original S manifest and cross-checks receipt hashes, the embedded manifest, source-image identities and observed records. Mathematics, thresholds and response computation are unchanged. All four rounds pass 63 loading identity checks each, and the original 19 self-tests pass. The [four-round frozen rejection](analysis-v1-schema-rejection/analysis.json) and [post-acquisition repair checks](post-acquisition-schema-repair.json) are preserved separately. This adapter was not pre-acquisition-frozen, and these checks do not establish successful full response analysis.

The existing adapter has completed a separately saved [post-acquisition diagnostic run](analysis-v2-post-acquisition-compatible-20261116/RESULTS.md): `DIAGNOSTIC_COMPOSITE_RESPONSE_GEOMETRY_CONFOUNDED`, `optical_acceptance=false`, and `inference_allowed=false`. Control drift is zero, but cross-system geometry exceeds the frozen gates and effective opacity remains unknown. E4 interval compatibility does not establish matching material or optical acceptance. Complete results and numerical arrays are preserved separately; frozen inputs and analyzer sources remain unchanged, with no new device acquisition or product changes.

The fixture and generated sources stay in this asset repository's [external research host](../slider-android-host/README.md). An explicit opt-in compiles them against a compatible Sleepy instrumentation host. Research sources do not enter the Sleepy product repository; ordinary builds do not load this entry point.

## Historical visual context

![Historical six-pose iOS/Android comparison](../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png)

This image comes from an earlier study. It is historical context, **not a paired result from these four conditions or an acceptance figure for this acquisition**. It cannot replace this directory's original evidence or subsequent analysis.
