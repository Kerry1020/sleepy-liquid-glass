# Slider finite color-response model diagnostic

Scope: existing original U matrices only, from the frozen eight-round RGB-star full100 calibration. No new acquisition, no production tuning, no native processing-order claim. Source analysis/NPZ/freeze identity is recorded before calculation. The baseline is encoded-sRGB and perturbation is finite +20 bytes, not a linear-light derivative. M may be read only for a previously declared generalization check, not used to fit a candidate.

Fixed measurements: preserve all nine output-row/input-column entries. Use original ROI and predeclared above-rail / capsule inset domains. Primary discrimination domain is y<422 and 0<=inset<3pt; also report 0..1, 1..3, 3..8, >=8, primary y<422 inset>=1 and full ROI. The capsule is a public-carrier approximation, not optical alpha. No data-derived mask or ROI is selected.

Compare expressive upper bounds before proposing a production candidate:

1. Scalar gain: Uhat = g I (one parameter per pixel).
2. Basic brightness+saturation: Uhat = a I + c 1 w^T, with fixed shader w=(.2126,.7152,.0722). Two free encoded finite-response coefficients per pixel; this is more permissive than one global saturation. Report implied brightness b=(a+c)/20 and saturation a/(a+c), with sign/weak-denominator flags. Coefficients are not automatically valid shader parameters. Equal offdiagonal entries within each input column, and common diagonal-minus-column coefficient, are necessary consequences.
3. Input-conditioned column gain plus shared luminance term: Uhat = diag(d_R,d_G,d_B)+c 1 w^T (four coefficients per pixel). This tests unequal channel gains while retaining basic saturation's repeated offdiagonals.
4. Output-conditioned saturation: Uhat = diag(a_R,a_G,a_B)+diag(c_R,c_G,c_B) 1 w^T (six coefficients per pixel). This keeps the two offdiagonal components within each output row in fixed luminance-weight ratio, and is still falsifiable.

Fit each linear model by fixed least squares; keep all signed residual entries, maxima, quantiles and RMSE. Additionally evaluate exact per-pixel Chebyshev feasibility at T=1/4/8 raw bytes using linear programming, not just the residual from a least-squares fit. Reject a model at a tolerance only if its feasible region is empty; LS error alone is not a rejection proof. One free parameter per 3x3 entry is a descriptive exact matrix, not a candidate.

Minimal localized candidate: if a simpler structural family remains compatible, fit a shared shape matrix to above-rail edge pixels, and mix it through fixed q(inset)=max(1-inset/8,0)^2 with per-pixel scalar g. Compare shared q-scaled rank-one luminance coupling against a q-scaled six-offdiagonal matrix with independent diagonal gain. Even/odd original-pixel checkerboard splits are an internal spatial cross-check only, not independent holdout; fit even and report both. No inference from a selected split or coefficient is allowed. The latter matrix is only a falsifiable encoded correction candidate, not recovered native layer order or displacement.

For a fitted local matrix family, retain an identity at q=0 for the extra color-coupling term. Reject adoption if required offdiagonal structure fails T4, if residuals remain concentrated at rim, coefficients require nonphysical/unstable gains, or the current M behavior contradicts the same response simplification. Current one-mask finite-step evidence cannot establish transfer to other colors, backgrounds, sizes, controls, motions or amplitudes, so no production parameter is authorized by a good fit.

Outputs: numerical JSON and NPZ under this new directory, a concise report with actual residuals, a synthetic self-test. All original study/freeze/receipts/PNGs remain untouched. No traces, xcresults or source PNG decoding is needed.

Implementation clarification before reading U: q is zero outside the declared public capsule (inset<0) as well as at inset>=8; no extrapolated outside correction. The local brightness+saturation candidate is Uhat=g(x)I+k*q*(I-1w^T), one shared k and freely fitted local scalar gain. The six-offdiagonal alternative uses freely fitted diagonal gains and six shared q-scaled offdiagonal coefficients. Also retain the necessary repeated-offdiagonal-within-column invariant independently of the particular w; violations cannot be fixed by merely choosing different luminance weights.
