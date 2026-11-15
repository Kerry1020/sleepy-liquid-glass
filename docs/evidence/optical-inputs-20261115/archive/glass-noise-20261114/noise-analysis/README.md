# RGB noise analysis: registered method, unopened holdout

This packet prepares a bounded static texture analysis. **No n01–n04 native or Android output has been decoded by this analysis.** These four independently seeded RGB-noise cases remain holdout, including both recorded themes. The fact that n05–n08 dot outputs were opened for a different analysis does not turn n01–n04 into calibration.

The existing `calibration/manifest.json` registers c01–c04 RGB-noise source PNGs. Their source files exist. The capture plan and native/Android indices register only n01–n08; no c01–c04 captured output is assumed to exist. The source inventory below is metadata, not an appearance result.

![Registered c01 calibration source only; no native or Android captured output](../calibration/c01_rgb_noise_s0.png)

This illustration is an original calibration **input**, not a glass rendering or evidence that a material matched.

`protocol.json` fixes spatial support, masks, channels, frequency bands, statistics and limitations. `input-inventory.json` preserves the relevant source/capture identities without copying images or precomputed appearance measurements. `analyze_noise.py` implements the array calculations and source-only/synthetic checks. This is **freeze-ready, pending root review**, not a frozen or completed evaluation. There is deliberately no captured-output evaluation CLI in this revision: the reviewed numerical method and future capture adapter must be frozen together before a one-time holdout run.

## Finite scope

- Compare each source separately with native REST, native repeat, historical Android baseline and fixed D46.5 candidate REST, once future evaluation is authorized. Use the declared world crop only; no fitted registration, resizing, color correction, lag maximization, frequency selection or candidate tuning.
- Keep four source IDs, two themes, native repeat, two Android variants and all five channels separate. Native repeat is capture stability, not another independent seed. Four source realizations are not a population sample of natural backgrounds.
- Report mean/code contrast, signed zero-lag correlation, signed spectral correlation and texture RMS/power ratios in every fixed ROI and band. Negative correlations and energy increases remain visible. Undefined low-energy cases stay null with their denominators recorded.
- Fixed geometric strata distinguish base interior, selected-lens interior, nominal edge and context-retaining Dock. Foreground and sparse-scroll context exclusions are conservative fixed rectangles, not recovered alpha coverage or proof of uncontaminated optics.

The masks and the finite ROI multiply the image before the FFT. Their spectral leakage, sparse support and native context/adaptation confounds are part of the result. The lowest band has limited cycles across the short Dock dimension. These statistics do not recover a material transfer function, physical blur, thickness, IOR, alpha, or cross-system physical equivalence. No pass/fail similarity score, confidence probability or 99.99% acceptance is produced.

## Checks available now

```sh
python3 -B analyze_noise.py --self-test --output /absolute/new-synthetic-check-directory
python3 -B analyze_noise.py --source-check --output /absolute/new-source-check-directory
```

The first command uses only constructed NumPy arrays and never opens a PNG. The second opens **only c01–c04 calibration source PNGs** after checking their registered hashes/profile/pixel hashes; it cannot open native, Android, n01–n04 or dot files. Both refuse to overwrite an output directory. Neither command changes historical freezes/results, creates caches, builds applications, captures a device, or modifies product parameters.

Before a future holdout run, root must review this method and the source/synthetic receipts, approve a capture adapter with strict metadata/world/profile checks, and freeze the complete implementation plus candidate/model identity. If outputs are subsequently used to revise the model or this method, those opened cases become calibration for that revision; a new disjoint test must be registered. Keep the original failure/result bytes. Do not quietly relabel an unopened test as calibration.
