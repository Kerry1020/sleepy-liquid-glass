# External observed-control integration build

The two asset-only studies were compiled together against the clean Sleepy tree matching upstream `2a0e4aeaf5029e7168fb15f49ca445a7481934b5`. They are not product-source changes, and a default Sleepy build never loads either init script.

| Attempt | Result | Interpretation |
| --- | --- | --- |
| [combined-20261116T011657Z](combined-20261116T011657Z/build.json) | Failed in 4.507s | The new slider overlay queried legacy `resolvedArtifacts` from `afterResolve`, forcing an untyped AGP project artifact selection; failure log retained. No Kotlin compilation or device execution. |
| [combined-20261116T012044Z](combined-20261116T012044Z/build.json) | Success in 11.961s | The overlay now checks component module versions through the resolution graph. Both diagnostic sources compile; the UI1.12.1 version requirement is retained. |

The successful test APK SHA-256 is `ed1aeb6e547479ae4f711b9a36a30aeeca876e10876ce9277b84df58ef933100`, 2,176,994 bytes. The existing main APK remains byte-identical: `566fc53eb6c28a0df7be03b7b07ee0ab8fd28a96b1f471f1669d7bbdbf3063b5`, 31,952,171 bytes. APKs are not copied into this repository. Source receipts, the exact overlay patch and both public logs are linked above.

The successful compiler reported one nullable-reflection warning at the renderer ID read in the slider observer; no compiler error. The observer checks the reflected method's primitive-long return signature. Runtime reflection, arithmetic consistency and timing checks still require actual device execution.

At this checkpoint ADB listed no connected device and no discoverable wireless service. Neither study has been installed or executed. No geometry, menu-material, natural-motion, optical or native-parity acceptance follows from compilation. The earlier failed language run and its original thresholds remain unchanged.
