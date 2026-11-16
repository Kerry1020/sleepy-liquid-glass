# Remaining Dock research hooks removed

The follow-up [PR #445](https://github.com/lingion/sleepy/pull/445) contains one application file, +3/−44, at `cea1aa3c96fd668c8a99d8b5fa4528c094d1aead`. It removes `DockBaseMaterialProbe` and `LocalDockLumaObserver`, neither of which has a product or remaining regression provider. The full original was published to this independent repository at `623132e6e9471d973bccc6ec40d1658cfab152ec` and its cloud blob/size verified before removal. No research file is added to Sleepy.

The old null path always draws the same 1dp border and passes the same `LiquidGlassStyle.pill` result. The cleaned path does so directly. Backdrop sampling, appearance hysteresis, input, layout, Material routing and factory/shader parameters are unchanged. Independent read-only reviews checked consumers and default-path equivalence.

[Local validation](build.json): `compileDebugAndroidTestKotlin` passed and 14 existing cases in `NativeDockLayoutTest`, `GlassDockInputContractTest` and `TabViewDockGeometryTest` passed. The [public log](build.log) retains the actual output. No device was used and this cleanup is not optical acceptance.

[Remote receipt](remote-pr445.json): all ten checks passed for the exact head. CI: https://github.com/lingion/sleepy/actions/runs/43787807793 ; debug build: https://github.com/lingion/sleepy/actions/runs/43787807755 . A normal squash merge after completion was refused by the base-branch policy. PR state remains OPEN/BLOCKED with no merge commit; `protect-main` is active and the current account cannot bypass it. No protection was changed and no administrator bypass attempted. The commit is published for review; its merge remains pending an authorized repository action.
