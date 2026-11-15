# Readout and limits

The frozen diagnostic executed; **it does not supply an identified edge tilt/curvature or a primary-boundary center-relative Android/native displacement curve**. No gate, support, branch rule or center reference was changed.

- Native primary center references at x54/324pt pass all 18 rows. The left center derivative is exactly zero. The right center inclination reaches only 0.010778°; its fixed slope bound is 0.0625, so this does not establish nonzero tilt.
- Every top24 and bottom24 region has zero eligible complete h4 derivative supports. Edge angle/curvature therefore remain unavailable. Native eligible edge points are sparse and include both displacement directions; their medians are not whole-trajectory evidence.
- Android x54/324pt centers each fail all 18 rows because of plateau spread and secondary peaks. Relative displacement remains unavailable. The x306pt secondary center passes Android, while its native center fails; it cannot replace a primary pair.
- The exact foreground union masks about 119pt of this 172pt pane. Unoccluded counts/failures are separately tabulated in `decision-summary.json`; failure counts overlap and are not independent trials.
- Screen and actual Window differ at the carrier fringe. Window alpha is retained. A screen being opaque does not identify the glass material silhouette, and no posthoc alpha gate was invented.

The original crops and all failed crossings are available for source/context diagnosis. They do not authorize fitting unique2Dmap, physical thickness or an equivalent optical model. A new runtime candidate can still use this identical frozen diagnostic; this analysis does not prescribe a new numerical sampling strength.
