# Body8 rim-baseline extraction

This uses the original full fixed straight/neutral/corner tracks and union masks; no new ROI is chosen. Body8 versus outline-zero16 changes Alert blur, so Alert deep pixels are expected to differ at this stage. The following rim-stage comparison will instead hold blur8 fixed and require strict original deep/body controls.

Both Sheet actual Windows are strictly zero difference; full display system-bar differences are retained. The shapes neutral top first four original pixel rows are strictly pixel-identical to outline-zero16. Its first row therefore still contains142/190 pure-white RGB255 pixels. Top0..<2pt error stays5.9596, and2..<4pt stays3.8351. Neutral left0..<2pt error improves9.2708→9.1111, right11.1458→8.6250; this does not fix the absent side highlighter.

Of48 fixed Alert corner slices,32 improve,15 worsen and1 is equal. Examples of worsened curves are coordinate top-left depth4.25pt (5.9853→6.6078 RGB mean error) and shapes top-left4.25pt (5.3676→5.8382). The complete raw/smoothed/D1/D2 corner and straight data are in `body8-corner-tracks.csv` and `body8-straight-tracks.csv`; all bins and per-slice errors remain in the matching metrics files. The `baseline` columns there mean outline-zero16; `candidate` means body8.

The first adapted analysis script accidentally replaced the baseline directory label while replacing output prefixes and produced an invalid self-comparison. That source, log and summaries are retained in `body8-self-comparison-error`. The corrected script changes output filename prefixes only; original captures, coordinates, masks and thresholds are unchanged. No body8 optical conclusion uses the self-comparison.

Next-rim scope and gates are frozen in `rim-next-frozen-plan.{md,json}`. The requested light Alert0/0/.06 CPU line plus.08 angular floor is a bounded two-parameter rim stage. Dark restoration and historical light final-combination regression are explicitly separated from same-source new-probe rim attribution.
