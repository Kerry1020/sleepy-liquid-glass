# Post-acquisition compatible analysis result — 2026-11-16

This is the first complete response run of the existing `analyze-compatible.py`, performed after acquisition. It is **not the pre-acquisition-frozen analyzer**, and it is **not product, native optical, animation, or interaction acceptance**. The original `analyze.py`, its schema rejection, all frozen source inputs and the original captures remain unchanged. Historical README statements that response analysis was pending describe the earlier archive state; this separate package records the later run.

The executable returned exit code **0**, with status **`DIAGNOSTIC_COMPOSITE_RESPONSE_GEOMETRY_CONFOUNDED`**, `optical_acceptance=false`, and `inference_allowed=false`. Exit 0 records completion of permitted diagnostics, not successful optical matching.

## Reproduction and provenance

Working directory:

```text
/Users/kerrylee/Documents/Codex/sleepy-liquid-glass/research/slider-android-response-20261116
```

Exact complete-analysis command executed:

```sh
python3 -B analyze-compatible.py --root /Users/kerrylee/Documents/Codex/sleepy-liquid-glass/research/slider-android-response-20261116 --output /Users/kerrylee/Documents/Codex/sleepy-liquid-glass/research/slider-android-response-20261116/analysis-v2-post-acquisition-compatible-20261116/report
```

The output directory did not exist before that command. It produced only `report/analysis.json` and the compressed numerical `report/response-arrays.npz`; no duplicate raw PNGs were generated.

Before response computation, the existing adapter was loaded with Python `runpy.run_path` and its unmodified `self_test`, `freeze_status`, `native_reference`, `load_round`, and `stable_geometry` functions were called. This gave 19/19 pure math/gate tests, 69 matching frozen asset hashes, four rounds with 63 bound identity checks each, one common screenshot shape, unchanged Android operating identity and stable eight-endpoint geometry. The adapter hash matches the recorded post-acquisition repair. AST comparison finds only `load_round` and `execute` differ from frozen v1; `execute` becomes identical after excluding its explicit compatibility-provenance entry. The complete preflight evidence is in `preflight.json`.

The original host source/APK freeze records are retained; this analysis did not operate on the Sleepy checkout, invoke Gradle, or use a device. Identity counts include repeated references across rounds; they are not counts of unique files.

## Gates and unresolved fields

All four ordinary flat-minus-pre-flat fields and the post-control-shape-minus-pre-shape field have maximum absolute RGB difference **0** on both the fixed original lattice and the once-sampled native grid. The declared ≤2-byte drift gate therefore passes without averaging or baseline reselection.

Within Android, observed owner/carrier bounds, centres and local affine elements, source origin and source sampling matrix have range 0 across the eight endpoints. Output affines are exactly identical. All eight original full100 PNGs declare sRGB metadata. This declaration is not proof of the internal colour pipeline.

Cross-system public-carrier bounds **fail** the frozen comparison gates:

| Quantity | Android minus native | Frozen maximum |
| --- | ---: | ---: |
| Left | −0.000809740 pt | 0.10 pt |
| Top | −0.052954986 pt | 0.10 pt |
| Width | +0.136697227 pt | 0.10 pt |
| Height | +0.105914712 pt | 0.10 pt |
| Centre X / Y | +0.067538873 / +0.000002370 pt | 0.10 pt |
| Carrier local-affine translation X / Y | −0.003858823 / +0.002487395 | 0.001 per element |

The recorded local-affine conventions retain their actual hierarchy/anchor differences; no registration or normalization was introduced. Android owner/carrier effective opacity is **unobserved**, so its cross-system delta remains null. It was not guessed to be 1.

## Fixed-grid encoded-byte diagnostics

Only full100 shape/flat pairs from each round enter the response arrays: 8 endpoints from the 48 acquired held endpoints. Other poses remain integrity-hashed context.

`U = global-G output − control-pre output` and `M = mask-G output − control-pre output`, using G output/input for the following scalar tables. Original signed int16 differences are retained. Each field is sampled once, bilinearly, onto the unchanged native 88×88 grid over world `[165.5,397.5,209.5,441.5)`. No image registration, outline scaling, gamma/profile conversion, denoising, or colour normalization is performed. The measured world-to-screenshot affine is diagonal `2.9750001`; world-to-producer factors are separately retained as `2.976` and `2.974512743628186`.

| Fixed domain | Pixels | U difference MAE / maximum | M difference MAE / maximum | Android-only nonzero M support |
| --- | ---: | ---: | ---: | ---: |
| Complete fixed ROI | 7744 | 1.315199 / 19.000000 | 0.095811 / 10.000000 | 58 |
| Above rail | 4312 | 0.568226 / 11.968791 | 0.148204 / 10.000000 | 40 |
| Primary native inset ≥1 | 1630 | 0.913485 / 5.048832 | 0.332047 / 7.831374 | 33 |
| Native rim 0≤inset<1 | 186 | 4.266237 / 11.968791 | 0.525901 / 10.000000 | 7 |
| Native exterior above rail | 2496 | 0.067183 / 10.736552 | 0.000000 / 0.000000 | 0 |
| Rail 422≤y<438 | 2816 | 2.341313 / 19.000000 | 0.036543 / 7.765072 | 18 |
| Below rail y≥438 | 616 | 1.853206 / 2.000000 | 0.000000 / 0.000000 | 0 |
| Secondary interior intersection | 1630 | 0.913485 / 5.048832 | 0.332047 / 7.831374 | 33 |

These are finite encoded-byte responses, not transmission, radiance, physical thickness, or a uniquely identified displacement.

## Conditional interval sensitivity

The unmodified endpoint allowances are E=1,4,8 bytes, with the shared-baseline residual allowance `2E`. Weak means `|U|≤2E`; weak contradictions remain reported. Incompatibility below means the two conditional common-alpha intervals do not intersect. Geometry already fails its material-isolation gates, so these counts are **composite pixel diagnostics**, not material-only rejection or acceptance.

| Fixed domain | Incompatible E1 / E4 / E8 | E4 weak native / Android / both strong | E4 native M>0: pixels / both strong | E4 nonzero M union: pixels / both strong |
| --- | ---: | ---: | ---: | ---: |
| Complete fixed ROI | 44 / 0 / 0 | 516 / 681 / 7063 | 316 / 314 | 374 / 370 |
| Above rail | 42 / 0 / 0 | 0 / 0 / 4312 | 282 / 282 | 322 / 322 |
| Primary native inset ≥1 | 32 / 0 / 0 | 0 / 0 / 1630 | 262 / 262 | 295 / 295 |
| Native rim 0≤inset<1 | 10 / 0 / 0 | 0 / 0 / 186 | 20 / 20 | 27 / 27 |
| Native exterior above rail | 0 / 0 / 0 | 0 / 0 / 2496 | 0 / 0 | 0 / 0 |
| Rail 422≤y<438 | 2 / 0 / 0 | 516 / 681 / 2135 | 34 / 32 | 52 / 48 |
| Below rail y≥438 | 0 / 0 / 0 | 0 / 0 / 616 | 0 / 0 | 0 / 0 |
| Secondary interior intersection | 32 / 0 / 0 | 0 / 0 / 1630 | 262 / 262 | 295 / 295 |

The E1 incompatible coordinates and all unclipped interval arrays are retained in `report/analysis.json` and `report/response-arrays.npz`. E1 has 44 incompatible pixels overall: 32 primary, 10 rim, and 2 rail. E4 and E8 have no interval incompatibilities; this is not a similarity percentage. In the primary native-M-positive subset, E4-compatible interval widths range 0.444444–0.933965, mean 0.611609, so the allowance leaves substantial ambiguity. Primary ratio differences among the 262 both-strong native-positive pixels still have MAE 0.114739 and maximum absolute difference 0.574706. Shared zeros are not used to suppress the positive-native and nonzero-union tables.

## Cross-channel and clipping diagnostics

For this checkpoint, both Android G-only perturbations have exactly zero output R/B response over the complete fixed ROI, including their original lattice. The frozen native global-G response reaches R=−14/B=−9 encoded bytes; its mask-G response reaches R=−8/B=−6. This records a cross-channel composite-response difference; it does not uniquely identify clipping, a colour transform, or transport.

No literal 0/255 channel values occur in any of the eight Android endpoint ROIs. Native literal-zero counts and all channel-specific endpoint clipping counts remain in the full report. The absence of literal endpoint clipping does not rule out internal clamps or offsets.

## Decisions supported by this run

- The existing four-round capture is stable enough for the prespecified byte-response diagnostics, with zero measured control drift and verified original identities.
- The E4 single-mask common-alpha surrogate does not falsify compatibility in these composite observations. It does not establish optical equivalence, refraction strength, opacity, a kernel or displacement.
- The measured cross-system carrier geometry fails its existing gate and opacity remains unknown. A material-only conclusion requires those issues to be resolved in a separately specified comparison; this run does not silently compensate for them.
- The rim U/M discrepancies and R/B cross-channel response difference are concrete locations/behaviours to retain for later falsifiable investigations. This result does not authorize parameter fitting, a new acquisition, a shader/default change, or product acceptance.

Post-run integrity verification is saved in `integrity.json`; artifact hashes, exact invocation, runtime versions and completion status are saved in `run-record.json`.
