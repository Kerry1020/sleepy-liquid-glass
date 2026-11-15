# Native Alert map — current16REST baseline

Existing public historical calibration only; no device, build, runtime edits,
noise/holdout reads or image copies. Resolve relative path rules against native_root.

## Provenance

Real SwiftUI `.alert("Native Alert")`, frozen NativeStage.swift:135–144.
iOS26.5/23F77, SE3 simulator B7EBD2CC-2FAE-449B-BB9B-1CB95F055764,
375×667pt at2px/pt; Xcode27.2/27B52. capture-manifest.json freezes five source files;
this pass rechecked their hashes, all8 original/rest byte identities, trace hashes,
input RGB hashes and750×1334 dimensions. All8 rest timestamps lie between their
first actual requested/confirmed callbacks. Separate AX reads are after quiescence,
not synchronous scanout proof. Sessions match requested traits; Reduce Motion,
Reduce Transparency and darkerSystemColors=false. REST does not prove motion.

Selected reference-configuration/exported PNG is authoritative: fine_grid8pt/.5pt;
opaque18pt RGB stripes;112pt tonal blocks; deterministic720×1280 synthetic landscape.
Generic session.backgrounds has legacy20pt/28pt descriptors; do not substitute those.
Same background has identical decoded RGB across light/dark.

Metadata: NATIVE_ALERT_EVIDENCE.md, capture-manifest.json, delivery-validation.json,
test-summary.json, attachments/manifest.json. Source snapshots under source/.
Contact sheets are resized navigation aids; measure original PNGs.

## Geometry and content

All8 native AX trees agree (half-open world LTRB in pt):

|Element|Rectangle|
|---|---|
|Alert|[27.5,257.5,347.5,429.5],320×172|
|Header|[27.5,257.5,347.5,349.5]|
|Title layout|[57.5,279.5,317.5,300]|
|Message layout|[57.5,307,317.5,345]|
|Action region|[27.5,349.5,347.5,429.5]|
|Cancel|[43.5,365.5,183.5,413.5],140×48|
|Confirm|[191.5,365.5,331.5,413.5],140×48|

AX is not recovered optical alpha. Native pixel center=(x+.5,y+.5)/2.
Current Android actual pane[55,515,695,859]px at density2 coincides with this AX
rectangle; material contour/AA still need separate observation. Use exported
actual Android slots and screen origins; never recenter/warp/resize to improve fit.

Native backdrop contains System sheet[126.5,286,249,319.5], System alert
[130,345.5,245,379], System menu[126.5,405,249,438.5] and3-tab Dock[51,572,325,634].
`before` is the composited scene; bare input is only the background renderer.
Different backing controls can influence blur/refraction even in empty Alert regions.

## Fixed analysis regions

Exterior/scrim ROI[32,176,343,220]pt => pixels[64,352,686,440]. It avoids native
foreground and Alert/shadow. All8 before screenshots equal bare input in this ROI,
decoded RGB RMSE0. Below is rest=C×before through-origin encoded RGB fitting;
this describes exterior response, not physical material transparency.

|Condition|Gain C|Residual RGB RMSE|
|---|---:|---:|
|color_stripes/dark|0.520043|0.314275|
|color_stripes/light|0.800070|0.280625|
|fine_grid/dark|0.519706|0.322386|
|fine_grid/light|0.800012|0.149852|
|synthetic_landscape/dark|0.519927|0.291815|
|synthetic_landscape/light|0.800004|0.282875|
|tonal_blocks/dark|0.519094|0.315432|
|tonal_blocks/light|0.800006|0.123711|

Thus native Alert exterior retains~.80 light/~.52 dark, matching historical Sheet.
Validate actual Android bare-source identity at this ROI first. Fit scrim here,
not inside the pane. Keep scrim-only changes separate from material/edge changes;
an analytically rescrimmed PNG is not a captured new rendering.

Body candidates: primary left[49.5,307,54.5,338] and right[320.5,307,325.5,338],
620native pixels each,22–27pt inward. Secondary empty gap left[60,350,110,359]
and right[265,350,315,359],1800pixels each. Exclude the union of actual native and
Android text/action boxes expanded2pt, report retained count, never move ROIs to
improve scores. These avoid direct content; blurred/refracted backing controls
remain possible. Report each ROI/channel separately: mean, spatial contrast, RGB
residual. Whole-pane foreground error is not material evidence.

Straight edge candidates: left x27.5/right x347.5 with tangent y307..338 and
inward normal−6..24pt; top y257.5 with tangents x62..104,x271..313, normal−6..20pt;
bottom y429.5 same tangents but only−6..10pt, because deeper samples hit actions.
Negative normals contain AA/shadow. Keep source phase and absolute coordinates;
report RGB, blue-opponent B−(R+G)/2, first/second derivative and crest/decay.
Displaced/blurred footprints can include controls absent from bare input; source
identity at the same coordinate alone does not isolate optical transport.

Corners stay separate: fixed horizontal scanlines at declared offsets from each
AX corner, with union foreground exclusion; these are raster scans, not recovered
normals to native contour. Existing menu-alert-visible-corners-20261113/REPORT.md
uses native fine_grid/light minRGB>210/215/220 in2–24pt for Alert34: color-level
candidates, not alpha. Its Android height differs+.773dp; use current geometry.

Stripe normal excitation exists on side edges, not top/bottom. Fine-grid phase is
periodic; tonal excitation depends on encountered transitions; landscape depends
on UV. Correlation lag is appearance phase, never unique physical ray displacement.
No physical thickness follows from bright-rim width. Historical8inputs are
calibration, not independent validation. Do not jointly tune scrim, geometry,
bevel, refraction and shine or infer99% parity from pooled scores.

## Reusable mapping

```json
{
  "native_root": "/Users/kerrylee/Documents/Codex/2026-11-10/1-sleepy-2-26-3-1/outputs/glass-native-parity-20261112/native-alert-optics-20261113",
  "path_rules": {
    "rest": "rest/{prefix}-alert-rest.png",
    "before": "rest/{prefix}-before.png",
    "ax": "rest/{prefix}-alert-rest-accessibility.txt",
    "original": "attachments/{attachment}",
    "bare_input": "traces/{run}/background-input.png",
    "session": "traces/{run}/session.json",
    "trace": "traces/{run}/trace.jsonl"
  },
  "conditions": [
    {
      "condition": "color_stripes/dark",
      "prefix": "alert-optics-color_stripes-dark",
      "run": "-_NativeReferenceTests_testAlertOpticsColorStripesDark_-C3D2D3F0-23C1-4F3C-92E5-C59DFB867DFA",
      "attachment": "28D48E53-2664-46E1-9DBA-BC237A8C93A7.png",
      "rest_sha256": "078833be7e6efba55438075322dce8f960da49fb06c27ed66263beb8a785123c",
      "input_png_sha256": "be768f215b3818c5c276f3fa136bc8c67409aab57f9046795730c801a3412b93",
      "input_rgb_sha256": "e8c1d0eced0d9f77a84b047f0be2d5ac02086298e800c85f7d8fdd78144be0b1",
      "session_sha256": "8372cb9a7e4612598e8d00e49be59ee371a5409ac90e69138ad396815f0e9841",
      "trace_sha256": "a4645825afa53f773af03d4b85b34e668a53924d9f27bd746d0498dadd8752aa"
    },
    {
      "condition": "color_stripes/light",
      "prefix": "alert-optics-color_stripes-light",
      "run": "-_NativeReferenceTests_testAlertOpticsColorStripesLight_-DF5EE42B-B627-491D-A7DA-EF394B966233",
      "attachment": "FCE33B1A-8D26-460D-A148-5911467B4F8E.png",
      "rest_sha256": "06bfae97ec012fd100c67c4ed31d23d8e38fd444544a23b1369b045e7af8f4b3",
      "input_png_sha256": "be768f215b3818c5c276f3fa136bc8c67409aab57f9046795730c801a3412b93",
      "input_rgb_sha256": "e8c1d0eced0d9f77a84b047f0be2d5ac02086298e800c85f7d8fdd78144be0b1",
      "session_sha256": "2b2ea52accf1324dddcdc5b091245d7a731081b3295401875163ff907be809ae",
      "trace_sha256": "38afe45e1026a267f35156077e1c2816e4a444422a70eb81163c656ff3fba46f"
    },
    {
      "condition": "fine_grid/dark",
      "prefix": "alert-optics-fine_grid-dark",
      "run": "-_NativeReferenceTests_testAlertOpticsFineGridDark_-9074F755-1054-4BF4-9846-37A874682A17",
      "attachment": "61603BBF-02C9-40D7-94EC-B8087781668F.png",
      "rest_sha256": "9801d4123ab80e0096921583d50ff780ea692e6b05c0852e39e0a2d7b84f90d9",
      "input_png_sha256": "0d82f51b359b4820cf1028a8e7618be0a55e1bc8d555c320125f2a8553fa4d54",
      "input_rgb_sha256": "0e250c29178d2678a9f352b5687eddd574e6c7d053f6e4e3f030ca813f1acb21",
      "session_sha256": "fff49a78c10d37429f99743da1b94d0599e7f400ae13ecddca55345b3cfe23f9",
      "trace_sha256": "f004a2f6eb1dc0df46d998a3c939e5bb1fa61c491697dfc0c17a8b332ec1be63"
    },
    {
      "condition": "fine_grid/light",
      "prefix": "alert-optics-fine_grid-light",
      "run": "-_NativeReferenceTests_testAlertOpticsFineGridLight_-19A0AC71-D3C3-490E-860A-92F161963E14",
      "attachment": "6830AA0A-95FF-4C2E-9474-DBDF5851870F.png",
      "rest_sha256": "5c1fda3052b4390e83db65641d4dbcb4f55a480ccb87b9ed7b387f2101b11566",
      "input_png_sha256": "0d82f51b359b4820cf1028a8e7618be0a55e1bc8d555c320125f2a8553fa4d54",
      "input_rgb_sha256": "0e250c29178d2678a9f352b5687eddd574e6c7d053f6e4e3f030ca813f1acb21",
      "session_sha256": "590f811f225cbc963a96ab0e03933aed2e17b0b0a756331e7cb72cba377a547a",
      "trace_sha256": "e2a73ed0b7b5de2c35c0bffd8e621f01ec3485394f86377c77d2fc663e2515ee"
    },
    {
      "condition": "synthetic_landscape/dark",
      "prefix": "alert-optics-synthetic_landscape-dark",
      "run": "-_NativeReferenceTests_testAlertOpticsLandscapeDark_-DB75FCA6-0E85-49D6-97E0-4D96AA7A8BD5",
      "attachment": "F6E8559D-C5F1-4C17-A113-A318CA090D81.png",
      "rest_sha256": "dd39be73418ff96c488e92b54651e9a484f23f4c7002df83540640c3121a37b3",
      "input_png_sha256": "9acd71617281acdb5e55d3cc0a74a24088a4f5d16f763fdb55ad6ed7a522deef",
      "input_rgb_sha256": "70c5e5e0720b58c2827d7f6c4e86151938523f89cd4b389b71ce157c8739899e",
      "session_sha256": "0a2f4ae91916043b6863820ff5716d29d57efa3612fcc24d4512d7ee1b8fdcdf",
      "trace_sha256": "1d3c9caf4788511024b1c1940f730677efc8090f52b86f2d3945a88d4aa4279a"
    },
    {
      "condition": "synthetic_landscape/light",
      "prefix": "alert-optics-synthetic_landscape-light",
      "run": "-_NativeReferenceTests_testAlertOpticsLandscapeLight_-21D50B16-8F8B-491C-8BAC-FA0E8E878875",
      "attachment": "4FCDBAF1-2C5F-428F-9670-AF38F7E4B2E7.png",
      "rest_sha256": "6b0642ab3c58a2977d938a4643e8bfd12cbfcda0cf8e3bb2e6fa13b33db12aca",
      "input_png_sha256": "9acd71617281acdb5e55d3cc0a74a24088a4f5d16f763fdb55ad6ed7a522deef",
      "input_rgb_sha256": "70c5e5e0720b58c2827d7f6c4e86151938523f89cd4b389b71ce157c8739899e",
      "session_sha256": "84321a4a2acb60e6d0ca63647443872a027cc95e0ed50392b66aed2d7176d178",
      "trace_sha256": "063a5590c266dbe3bb0586d45500f893cdb1b1ca31e06edba6bc15e0ec6bbd13"
    },
    {
      "condition": "tonal_blocks/dark",
      "prefix": "alert-optics-tonal_blocks-dark",
      "run": "-_NativeReferenceTests_testAlertOpticsTonalBlocksDark_-9DA553ED-647D-4BF7-B7BD-8A84787160A9",
      "attachment": "27B8BF84-1B79-43F0-9BAF-162914D1E98D.png",
      "rest_sha256": "3f177a89619b363dd23fe30e99edcf6088a7bda31d7dcc3770fff7bea8ff95d7",
      "input_png_sha256": "0a2a4b089c512067a1f606129e4e9d0c37a401f84dc556c7f9fcac396c72e4d9",
      "input_rgb_sha256": "12d47f5bf9ee4ddb90a9e1884d1385a09c32478a3b5d2afaf3a49b7e649676d3",
      "session_sha256": "48a8c2462be1eac3276531e74fe7957d59952732e5a6f18e3f174a74bb30897b",
      "trace_sha256": "99a912e3757814a53fc3f765ebc3ce23527927e1b67c883d48e04031dc519ff6"
    },
    {
      "condition": "tonal_blocks/light",
      "prefix": "alert-optics-tonal_blocks-light",
      "run": "-_NativeReferenceTests_testAlertOpticsTonalBlocksLight_-99AE5E30-5F47-4C03-ACF6-FBC72CAECF75",
      "attachment": "753DB2D2-43A9-4549-8221-EC3E93C0F020.png",
      "rest_sha256": "b321b9085839f3007c70bc701b42d4b968c5b86a46095a17ca264cc06cf29581",
      "input_png_sha256": "0a2a4b089c512067a1f606129e4e9d0c37a401f84dc556c7f9fcac396c72e4d9",
      "input_rgb_sha256": "12d47f5bf9ee4ddb90a9e1884d1385a09c32478a3b5d2afaf3a49b7e649676d3",
      "session_sha256": "e0df5d9450fc9c0a04a57bd14d4eb3f3f902dd87f72a7599dbd0684a7fafbb34",
      "trace_sha256": "e4f9f996f1f3a8456d24ea0a38c90cf90a976286bb0ec63539eda3b8a87b972a"
    }
  ]
}
```
