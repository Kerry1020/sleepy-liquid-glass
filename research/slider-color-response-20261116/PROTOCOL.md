# Full100 RGB perturbation diagnostic — frozen before capture

This is a calibration diagnostic of the iOS 26.5 native Slider, not a product change, independent holdout, physical thickness measurement or optical acceptance. The app and production r2 material are unchanged. Only the native test's full100 selection is narrowed; no other pose or control is acquired. The seven-point source is not consumed.

The baseline is the original multicolor five-point `st01_rgb_star_d16`, SHA-256 `9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724`, **not** the G128 control from the preceding midpoint experiment. Its 16pt shape, vertices, three regions, coverage16 masks, original 750×1334 pixel grid, sRGB ICC and coordinates remain unchanged. The previous five red midpoint anomalies may be named as fixed spatial probes; this changed color baseline does not repeat or uniquely explain that earlier contrast.

## Exact acquisition and sources

Round order is `control-pre`, `global-R`, `global-G`, `global-B`, `mask-R`, `mask-G`, `mask-B`, `control-post`. Each round has one shape and one ordinary-flat held endpoint at full100: eight rounds, sixteen sessions, exactly two verified endpoints and one verified shape/flat pair per round. Pre/post are repeated operating-state checks, not independent samples. Pre is the fixed arithmetic baseline; no averaging or post-result baseline choice is allowed.

Inputs live at `inputs/rounds/{round}/shape-spec.json` and `inputs/rounds/{round}/inputs/manifest.json`. Acquisitions live at `rounds/{round}/native-r1/endpoint-verification-strict.json` and `index-strict.json`. The strict verifier still verifies the delivered input, complete held screenshot bracket, presentation stability and original source identity, but requires only the declared full100 stage.

For channel j, the global variant adds exactly 20 encoded bytes to that channel of every baseline pixel. The masked variant adds `floor((20*coverage16+8)/16)` to that channel, using the original `left_blue` coverage-count mask, SHA-256 `0520b9b21148d9b0febef0f706c5ae9766d6ba3f6600d483e6d0f1980083202d`. The other two channels are byte-identical. Source values 48/128/232 become at most 252, without input clipping. The mask increment is identical for all three channel variants; its maximum rounding error relative to 20×coverage is 0.5 **input** byte, not a bound on native output error. This is an encoded-sRGB perturbation, not a constant radiance perturbation.

Every paired flat remains the exact original `st00_flat128`, SHA-256 `6e4291536355bff3dae7dee3957eec96bf4f3efc7566dd4257721a635ad8340b`. It measures geometry and drift only. No perturbed flat is substituted, and ordinary-flat differences are **not subtracted from the response**, because doing so could remove the DC response under examination.

## Acquisition and comparability gates

Missing required fields, failed strict status, unexpected/duplicate stages, nonopaque or non-RGB8 screenshots, mismatched source/spec/manifest/PNG hashes, changed ICC, or a source not matching the exact prescribed perturbation reject analysis. Only current receipts, indexes, original PNGs and input metadata are read; no old trace or xcresult is read and no acceptance is invented for omitted evidence.

The screenshots must be original 750×1334 images at 2px/pt, world origin (0,0), source world 375×667pt, fixed canvas (0,0,375,667), calibration/light interface, and the same recorded operating settings. No resampling, registration, translation, color-profile conversion, private control mutation or inverse geometry repair is allowed.

Across all sixteen shape/flat observations and their presented owner/carrier samples, require:

| Quantity | Maximum range |
|---|---:|
| Each actual carrier/owner bound and center | 0.10pt |
| Each owner/carrier presentation affine element | 0.001 |
| Public effective opacity | 0.01 |
| Source origin and source-to-pixel matrix element | 1e-8 |

Each round's ordinary-flat minus pre-flat must have absolute maximum ≤2 bytes in **every RGB channel across the entire fixed ROI**. Post-shape minus pre-shape has the same maximum gate. There is no pooling over rounds and no p99-only escape. Full signed minima/maxima, quantiles, energy and counts above 1/2/4/8/16/24 are saved. A failed gate produces a rejection report and no response fit. A nonzero difference inside a gate remains a stated confound; these checks do not bound every unobserved transient or the optical effect of a permitted pose difference.

## Fixed measurements and null hypothesis

The original integer-pixel ROI is `[331,795,419,883]` (Python half-open x0,y0,x1,y1), corresponding to world `[165.5,397.5,209.5,441.5]`. Pixel centers are `((column+.5)/2,(row+.5)/2)`. Report the complete ROI and separately `y<422`, `422≤y<438` (rail-confounded), and `y≥438`. The primary descriptive domain is above the rail and carrier-capsule inset ≥1pt; the rim and remaining ROI are retained.

Inset uses the pre-shape public carrier rectangle's declared capsule approximation, not recovered native alpha. This experiment explicitly freezes bins `[0,.5,1,1.5,2,3,4,5,6,7,8,10,14,20]`; these are a new diagnostic binning and differ from the preceding midpoint plan. Outside/negative inset is reported separately through the complete and rim domains. No new result defines a mask, cutoff or bin.

For output channel i and perturbed input channel j, retain original-byte matrices:

```text
U_ij(x) = global-j-shape_i(x) − pre-shape_i(x)
M_ij(x) = mask-j-shape_i(x) − pre-shape_i(x)
Jglobal = U / 20; Jmask = M / 20
```

Rows are output R/G/B; columns are input R/G/B. These are finite encoded-byte secants, not an identified linear-light color matrix or infinitesimal Jacobian. All nine signed components, their individual statistics, all raw ROI pixels, and original geometry are retained. No aggregate substitutes for a component's regression.

The prespecified **common nonnegative spatial kernel plus local color mix null** is: at each output x, the encoded response is affine with a fixed local 3×3 mix and a fixed shared nonnegative spatial kernel for all RGB channels over these perturbations. A necessary consequence is the existence of one scalar `0≤alpha(x)≤1` such that `M(x)=alpha(x)*U(x)` for all nine entries. This is an explicitly testable restriction; it is **not an assumption that the actual native byte pipeline is linear**.

At each pixel, intersect the nine intervals satisfying `|M_ij−alpha*U_ij|≤T` with `[0,1]`. Empty intersection is incompatibility with this bounded null at that tolerance. **T=4 raw bytes is primary**; T=1/8/16/24 are always reported together. T=1 is only the worst-case final nearest-8bit readout error for the shared-baseline contrast `mask−alpha*global−(1−alpha)*pre` when alpha is in [0,1]; it excludes input rounding, transfer functions, internal processing, drift and pose error. No threshold is selected from results.

The same interval calculation is prespecified separately for each input column (one alpha per input) and each output row (one alpha per output). Report all groups. A common failure with column compatibility is consistent with input-conditioned spatial responses; row compatibility is consistent with output-conditioned responses. Neither result identifies processing order, and near-diagonal color response can make both compatible.

For descriptive residual maps only, compute the minimum possible maximum absolute residual over alpha∈[0,1], and its corresponding interval midpoint; this minimizes a scalar constraint, not a spatial registration or a new runtime parameter. Keep the nine signed residual components, minima/maxima, quantiles and energy. Pixels with `max|U|≤4` have unresolved uniform gain: do not publish an identified alpha or elementwise ratio. Their interval constraints and any strong masked-response contradiction remain visible. If both U and M are ≤4, mark response unresolved. Compatibility is not identification or acceptance.

## Interpretation limits and execution

Failure can arise from channel-dependent sampling, encoded/linear transfer, finite-step nonlinearity, clipping/floors, content-adaptive tint or gain, color processing before sampling, different color mixes in directly visible and optical layers, or residual motion/drift. Uniform offsets change a whole scene while the mask changes a small colored region. These stimuli cannot isolate those causes. A single mask constrains an integrated spatial response, not a unique displacement, blur kernel, alpha, physical lens thickness or complete 3×3 pipeline. Passing cannot prove universal linearity or equivalence across shapes, backgrounds, sizes, speeds or controls.

### External freeze and capture identity binding

Before capture, write `freeze.json` outside the files it hashes. Its required top-level identity schema is:

```json
{
  "files": {"relative/study/path": "lowercase SHA-256"},
  "prepared_native_files": {"project-relative/path": "lowercase SHA-256"},
  "native_binaries": {"DerivedData-relative/path": "lowercase SHA-256"},
  "simulator": {"udid": "...", "runtime": "...", "build": "..."}
}
```

`files` covers the current `PROTOCOL.md`, executing `analyze-response.py`, `capture-native.py`, `source-verification.json`, every narrowed `native-tools/*.py`, all current files under `inputs`, every round's spec and manifest, every manifest PNG and every spec-referenced source/coverage/support PNG. It also includes `../slider-fixtures/SOURCE-MAP.json` and `../slider-fixtures/tools/native-glass-reference/verify-static-optics.py`. Hashing loader-compatibility source files does not decode their pixels or make them scheduled observations. Every listed member is rehashed, including additional frozen files. Parent-directory entries are allowed only when their resolved path stays inside this asset repository; absolute paths, noncanonical paths, duplicate resolved aliases, missing files and a self-reference to `freeze.json` reject analysis. Actual analysis requires the study's analyzer to be the currently executing file.

The nonempty `prepared_native_files` map identifies the prepared native project. The nonempty `native_binaries` map identifies every file in both built `.app` products, including the app's actual `.debug.dylib` code and test bundle, plus the selected `.xctestrun`; no fixed map-entry count is assumed. These two maps use canonical relative paths without parent traversal. The capture runner verifies those file bytes before capture. Analysis compares their full frozen maps with the recorded capture maps; it does not require `.local/DerivedData` or prepared build files to survive transfer to another device.

Each `rounds/{round}/native-r1/receipt.json` must be a completed capture for that round with exactly two held endpoints and one pair, finite ordered start/finish times and no failed recorded command. It must contain:

- `freeze_sha256`, the hash of the exact current `freeze.json` bytes;
- `prepared_native_files` and `native_binaries`, exactly equal to the frozen maps;
- `simulator_identity:{udid,runtime,build}`, exactly equal to `freeze.simulator`, with the retained `simulator` string equal to that UDID;
- `spec_sha256` and `manifest_sha256`, matching the current validated round inputs;
- `analysis_artifacts`, a canonical capture-directory-relative path → SHA-256 map binding the strict index, strict verification receipt and both original shape/flat PNGs. The runner also includes capture events and native session metadata. All listed artifacts are rehashed, not only the required subset; artifacts escaping the capture directory or referring to the capture receipt itself are rejected.

The strict receipt's verifier and PNG-validator identities must match the current frozen verifier files. Every output image is thus bound through `capture receipt → current freeze → current protocol/analyzer/source/native identities`, and through `capture receipt → strict index/receipt/PNG hashes`. A missing field, stale script/source/binary/simulator identity, changed output or missing required frozen/output member rejects response analysis. Each round’s capture/freeze/artifact binding is checked before that round’s captured PNGs are decoded. The report retains the freeze identity, verified current-file count, capture-receipt identities and full recorded native/artifact maps.

This chain checks recorded identity consistency, not cryptographic proof of trusted acquisition time or protection against a coordinated rewrite of freeze, receipts and evidence. The freeze must be preserved externally before acquisition; no timestamp inferred from the analyzed pixels establishes that chronology. No old optical result is read to select parameters.

```sh
python3 analyze-response.py --self-test
python3 analyze-response.py --root /absolute/path/to/slider-color-response-20261116
```

The default output is a new `analysis` directory; an existing output is rejected. The `--self-test` branch never requires the study freeze, capture outputs or native build products. Synthetic tests exercise known common/input-dependent/output-dependent kernels, unresolved responses, drift, geometry/source mismatch, missing evidence, frozen-file membership/hash/path gates, capture freeze/native/simulator identity and output artifact binding without pretending to be optical captures. Its temporary synthetic text files are removed after the checks. The evidence output is `analysis.json`, original ROI and raw/J/residual/interval arrays in `original-pixels.npz`, and explicit incompatibility coordinates. It does not modify captures, sources or product code.
