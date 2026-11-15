# Contributing

Use a small pull request with a concrete reproduction and describe the affected
control, input and background. Run:

```sh
./gradlew :runtime:assemble :runtime:testAndroidHostTest :sample:assembleDebug
```

A behavior fix should preserve controlled values, cancellation, disabled input
and accessibility. Keep Material routing in the consumer application. Optical
changes need distinct backgrounds and separate center, edge, contour and motion
evidence; a passing callback test does not prove visual parity.

Do not commit APKs, Gradle caches, phone exports, private data, Apple implementation
code or raw reference videos. Small synthetic-fixture control crops may accompany
a measured result: remove system bars and identifiers, preserve visible mismatches,
and record original hashes and every crop/scale operation in the evidence manifest.
Retain source notices. No release or package publication is required for
a normal contribution.

## Evidence for material or motion changes

Keep a contribution small enough that another developer can reproduce its actual
claim. Run checks relevant to the changed mechanism and record the source commit,
command and result. The build command above is the independent-source baseline;
an application build or screenshot is not independent-backend optical acceptance.
The current [validation record](VALIDATION.md) separates those scopes.

For an optical experiment, preserve the exact input bytes and their hashes,
actual source / pane geometry, requested and effective theme, foreground masks,
background hierarchy, fixed sample coordinates, color metadata and decode path.
Freeze the regions, comparisons and decision rules before viewing new output.
Report raw color, smoothed profiles and derivatives separately; retain every
reference, background-specific regression, clipping check and unresolved width.
Subpixel interpolation is not new image resolution, and overlapping probes are
not independent trials. The [panel study](docs/panel-material-study.md) illustrates
why eliminating clipping does not establish better corner derivatives.

For dynamic controls, record actual delivered DOWN / move / UP / cancel input
and actual frame timestamps through the complete return to rest. Keep body size,
layout, content and background as separate axes. A scaled screenshot does not
create a native size, a requested velocity is not a delivered trajectory, and
native-only observations are not Android parity. Contributors need not run a
long all-control matrix for a focused fix.

Maintain distinct labels for a proposal, prepared schema, collected run,
executed analyzer and accepted result. Preserve failed frozen gates when a
later metadata review changes interpretation; do not silently reclassify an old
failure as a pass. Publish numerical data, processing instructions and a useful
figure with a measured result; identify any raw archive that is not distributed.
Do not claim physical thickness, a unique source map, a similarity percentage
or every-millisecond agreement without evidence that identifies that quantity.

Use the [controlled optical study index](docs/controlled-optical-studies.md) to
locate related assets and record the exact stage a contribution extends. Keep
new observations separate from earlier calibration and from unexecuted plans.
