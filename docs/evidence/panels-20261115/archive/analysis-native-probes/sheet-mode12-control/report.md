# Phase A: true-radius input at 12 preserves actual Windows

The four accepted light REST actual Window images are raw RGBA pixel-identical between `panels-alert-rim-bounded-20261115` and `panels-sheet-radius12-control-20261115`. Both Sheet Windows and both Alert control Windows have zero changed pixels. The two plain-background Windows also have zero changed pixels. Window placement, pane geometry, source mapping, unit basis, foreground slot rectangles, density and font scale are exact.

This establishes an unchanged-rendering mode12 control in the fixed fixture. It does not improve or validate the material. The native-comparison limitations of the prior Sheet12 response remain, and no new material charts were generated.

All composited-display differences are retained, with exact row-band coordinates in `exact-control-comparison.json`. They lie within y35..60 and, for some captures, y1312..1319, inside the declared top/navigation system-bar insets. None occurs in y[80,1302). No system overlay was removed or registered. Exact Window equality is the control conclusion; full-display equality is not claimed.

Raw RGB equals ICC-normalized sRGB for every compared screenshot. Accepted input file hashes and the revised before-decode plan were bound before phase A's first pixel decode. Rejected-display images were not decoded. No resize, recentering, warp, fitting, source substitution or duplicated screenshot was used.

The registered next step is the API-input engineering perturbation 12 → 10, with phase A as its direct control. The exact12 shared-band route and the10 local-preblur fallback are different execution routes, despite using the same true-radius API. Therefore phase B will measure the deployed API response including that deterministic route change; it cannot isolate a common-Gaussian-path radius effect. Root must bind `GlassHost.kt` and `GlassFilterBands.kt` source hashes in the next build freeze before phase B decode. Radius6 is excluded. Dark retains the original factory/null branch by the declared implementation scope; no dark pixel comparison was captured or claimed.
