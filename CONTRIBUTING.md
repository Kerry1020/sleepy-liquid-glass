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

Do not commit APKs, Gradle caches, phone exports, private data or Apple reference
media. Retain source notices. No release or package publication is required for
a normal contribution.
