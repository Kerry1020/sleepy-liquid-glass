# Third-party notices

Sleepy Liquid Glass contains work extracted from the GNU GPL v3 Sleepy project:
https://github.com/lingion/sleepy

The `runtime` implementation contains Kotlin/AGSL adaptations of FLClash by
chen08209, licensed under GNU GPL v3. Original source references and explanatory
comments remain in the imported files.
https://github.com/chen08209/FlClash
Full text: third-party/notices/FLClash-GPL-3.0.txt

The rounded-superellipse implementation adapts Flutter engine geometry under
BSD-3-Clause. Copyright notices and the original adaptation notes are retained.
Copyright 2013 The Flutter Authors. All rights reserved.
Pinned source: flutter/flutter at adc901062556672b4138e18a4dc62a4be8f4b3c2,
engine/src/flutter/impeller/geometry/round_superellipse_param.cc and
engine/src/flutter/impeller/geometry/rounding_radii.cc.
Full text: third-party/notices/Flutter-BSD-3-Clause.txt

LiquidGlassPhysics.kt adapts Flutter framework SpringDescription and
SpringSimulation under BSD-3-Clause.
Copyright 2014 The Flutter Authors. All rights reserved.
Pinned source: flutter/flutter at adc901062556672b4138e18a4dc62a4be8f4b3c2,
packages/flutter/lib/src/physics/spring_simulation.dart.
Full text: third-party/notices/Flutter-Framework-BSD-3-Clause.txt

Official pinned file URLs, byte counts and SHA-256 hashes for both Flutter
adaptations and their respective licenses are recorded in
[provenance/flutter-sources.json](provenance/flutter-sources.json).
This revision is the verified attribution reference; the imported physics file
does not record its historical Flutter acquisition revision.

## Imported notice paths

The imported runtime files retain their original bytes, including references
written for the Sleepy app's assets layout. Resolve those historical references
against the notice files in this source distribution:

| Original reference | Notice in this repository |
| --- | --- |
| `assets/third_party/notices/Flutter-BSD-3-Clause.txt` | [third-party/notices/Flutter-BSD-3-Clause.txt](third-party/notices/Flutter-BSD-3-Clause.txt) |
| `app/src/main/assets/third_party/notices/Flutter-BSD-3-Clause.txt` | [third-party/notices/Flutter-BSD-3-Clause.txt](third-party/notices/Flutter-BSD-3-Clause.txt) |
| `app/src/main/assets/third_party/notices/FLClash-GPL-3.0.txt` | [third-party/notices/FLClash-GPL-3.0.txt](third-party/notices/FLClash-GPL-3.0.txt) |
| `third-party/notices/FLClash-GPL-3.0.txt` | [third-party/notices/FLClash-GPL-3.0.txt](third-party/notices/FLClash-GPL-3.0.txt) |

The separate framework notice above supplements the engine notice; it does not
replace its 2013 copyright. When distributing binaries, retain the applicable
notices in the accompanying documentation or other distribution materials as
required by their license texts. The path mapping does not imply that the notices
are packaged automatically into the runtime AAR or the sample APK.

## Backdrop and dependencies

The `backdrop` module begins from Kyant0/AndroidLiquidGlass tag 2.0.0, commit
bebb11a91bd97bf1dabde479f3b332ad9898731f, under Apache-2.0. Only four files are
locally adapted for the extracted runtime: BackdropEffectScope.kt,
DrawBackdropModifier.kt, backdrops/LayerBackdrop.kt and
backdrops/LayerBackdropModifier.kt. Their original portions retain Apache-2.0;
newly authored adaptations have their stated GPL notice. The baseline manifest
contains exact original Git blob identities, not hashes of the modified files.
https://github.com/Kyant0/AndroidLiquidGlass
Full text: backdrop/LICENSE and third-party/notices/Kyant-Backdrop-Apache-2.0.txt

The SleepDown-customized backdrop used in the Sleepy app is not included here.
This standalone backend does not claim its additional features or equivalent
GPU output. Runtime source bytes are preserved from Sleepy; provenance metadata
does not erase or replace any upstream copyright or license.

External dependencies keep their own licenses, including AndroidX Compose and
Material (Apache-2.0), Kyant Shapes (Apache-2.0), kotlinx.coroutines (Apache-2.0),
and Material Color Utilities (Apache-2.0). They are resolved by Gradle and not
vendored as binaries.
