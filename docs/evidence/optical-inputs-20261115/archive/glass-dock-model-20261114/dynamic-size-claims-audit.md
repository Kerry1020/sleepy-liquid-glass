# Multi-size and complete-action frame claims audit

The reviewed documents do not falsely claim that the new v4 multi-size, complete-action, all-actual-frame study is complete. GOAL and v4 agree on the main requirements. The public library roadmap is less specific than v4, and VALIDATION should distinguish completed Dock REST photometry from outstanding transport/Sheet work.

This was a source/document-only review. No device, build, Git, image decoding, analyzer/checker execution, or new agent was used. Only this audit file was added; original documents were not edited. Line numbers below refer to the source hashes listed at the end.

## Status that the evidence supports

| Scope | Accurate status | Source |
| --- | --- | --- |
| Existing static studies | Dot, isolated-shape and plain-scroll captures/analyses have explicit local scopes and unresolved limitations; they are not product acceptance | R/GOAL.md:16-18 |
| Mechanism packet | Seven actual passing JUnit jobs, 44 REST scenes, 44 backgrounds and 176 PNGs; fixed-size static calibration only | M/mechanism-capture-integrity-review.md/json |
| Source/native size plan | 108 source geometry conditions on 18 plates and 47 planned native configurations are declarations, not measured support | R/GOAL.md:13,30,36; N v4 MD:22,77-95 |
| Native size axes | body_size, layout and content remain separate. Intrinsic Toggle has one real body size. Other public sizing support must be measured, including unavailable/ignored requests | N v4 MD:77-95 |
| New v4 dynamics | Unfrozen, ungenerated, uncaptured proposal; generator, driver, native sizing support and dynamic tracker gates remain outstanding | N v4 MD:3,89,159,183; JSON /status, /execution, /documentation_contract/new_capture_authorized |
| Historical motion subsets | Native hold/release frames, some held carrier trajectories and empirical deformation models do exist. These do not constitute new v4 full-action/frame coverage | L README.md:60-65,133,173,214-216,225-229; README.en.md:133,173,216-220,228-232 |
| All actual frames/instances | Independent original PTS ledger, every actual frame and every actual component instance/lifecycle status are future capture/analysis contracts, not proof of an implemented collector/tracker | R/GOAL.md:29-31; N v4 MD:143-145,153-155,181-183 |
| Action completeness | 64 x 6 seconds is an initial screen. Unsettled actions remain incomplete and have finite follow-up. The 1392 nominal slots are conditional staged accounting, not permission to run a large matrix | R/GOAL.md:36; N v4 MD:71,97-105,119-121 |
| 95 protocol checks | Existing receipt and current MD/JSON hashes agree. These are protocol math/mutation/synthetic metadata checks, not measured native sizing, collector/tracker or dynamic acceptance | R/GOAL.md:36; N v4 MD:189; M/protocol-v4-review-receipt.json |

R = /Users/kerrylee/Documents/Codex/2026-11-10/1-sleepy-2-26-3-1

M = R/artifacts/glass-dock-model-20261114

N = R/artifacts/glass-noise-20261114; v4 MD/JSON = next-stage-dynamic-controlled-shapes-protocol.md/json

L = /Users/kerrylee/Documents/Codex/sleepy-liquid-glass

Root's newly proposed native-size-support static calibration needs a separate source/build/packet identity. Preparation is not a completed measurement. Completing that calibration would not itself start or complete v4 dynamic testing, and must not mutate the old M executable/source freeze.

## Exact sentences to clarify

These are documentation precision/synchronization changes, not blockers for the current static diagnostic analysis. They do not justify another device matrix.

### 1. Chinese public roadmap omits the expanded plan

Path: /Users/kerrylee/Documents/Codex/sleepy-liquid-glass/README.md:274

Original:

> 接下来优先提取完整控件适配器，补齐 Toggle/Tab 的自然动态、滑杆释放与不同宽度、Dock 多背景材质及嵌套源覆盖，再建立公开后端自身的配对基准。

This is not a false completion claim. It explicitly identifies only slider width variation, however, and does not communicate the new seven-family body/layout/content and complete-action/all-frame plan.

Suggested replacement:

> 接下来先完成静态材质校准与原生尺寸能力核查，再分阶段补齐 Dock、分段 Tab、Toggle、单头滑杆、单选菜单、对话框/半幅弹窗和按钮的完整适配与配对验证。新动态 v4 仍是未冻结、未采集的计划：分别登记真实本体尺寸、布局与内容，保留固定 intrinsic Toggle 的一个真实本体尺寸，记录每项完整动作从输入前到回稳的所有实际帧及全部组件实例。现有历史运动子集不算这项覆盖完成，协议检查通过也不等于动态验收。

Only link a v4 plan after it is actually published in L. Do not publish a local R path as a usable public evidence link or describe 47 planned configurations as 47 supported configurations.

### 2. English roadmap needs the same update

Path: /Users/kerrylee/Documents/Codex/sleepy-liquid-glass/README.en.md:285

Original:

> Next work prioritizes complete control adapters, natural Toggle / Tab dynamics, slider release and width variation, Dock material across distinct backgrounds, nested-source coverage, and paired benchmarks for the public backend itself.

Suggested replacement:

> Next work first completes static material calibration and verifies genuine native sizing support, then stages complete adapters and paired validation for Dock, segmented Tab, Toggle, single slider, single-choice menu, dialog/half sheet, and button. The new dynamic v4 study remains an unfrozen, uncaptured plan: body size, layout, and content are separate axes; intrinsic Toggle retains one actual body size; every complete action retains all actual frames and component instances from pre-input through observed settle. Historical motion subsets and passing protocol checks do not complete this coverage or establish dynamic acceptance.

### 3. VALIDATION groups completed and unfinished static work

Path: /Users/kerrylee/Documents/Codex/sleepy-liquid-glass/VALIDATION.md:24

Original opening:

> Eight new preregistered synthetic inputs, approximately seven designed families, await complete quantitative/transport review.

This is not strictly false because complete review is still pending. It is less precise than both READMEs at line 106, which state that fixed four-item Dock REST photometry is complete and retains 12 review cells, and line 110, which leaves independent transport/topology and Sheet verification outstanding.

Suggested replacement opening:

> Fixed-size four-item Dock REST photometry on eight preregistered synthetic inputs is complete, with the 12 engineering-review cells retained and no accepted candidate or aggregate score. Independent transport/topology review and Sheet verification remain outstanding.

Keep the existing exclusions for size families, interactions, acceleration, elastic release, independence and per-millisecond equivalence. Add:

> The new multi-size, complete-action, all-actual-frame dynamic v4 study is still a draft; protocol consistency checks are not native sizing, collector, tracker, or dynamic acceptance.

### 4. Optional explicit gap row in both READMEs

Insertion points: README.md:225 and README.en.md:228, after the existing overall-equivalence row. Preserve that row's incomplete verdict.

Suggested Chinese row:

> 真实多尺寸与完整动作全帧 | 尚无完成的跨控件覆盖验收；新 v4 为未执行草案，body/layout/content 分开，关键帧展示和协议检查不能代替实际覆盖。

Suggested English row:

> Genuine native sizes and complete-action frame coverage | No completed cross-control coverage acceptance; new v4 remains an unexecuted draft. Body/layout/content are separate, and keyframes or protocol checks do not replace actual coverage.

## Correct limitations to retain

- R/GOAL.md:13,29-31,36 and N v4 agree on size axes, all instances/frames and incomplete-action policy. No correction is needed to those requirements.
- N v4 MD:3,89,153,183,189 and JSON explicitly distinguish proposal, unmeasured support, uncaptured work and protocol-only checks. No false completion claim was found.
- L README.md:9,60-67,96,110,133,173,214-216,225-233; corresponding English limits; and VALIDATION.md:7,12,20 correctly limit historical build/model/figure results.
- Do not replace 'no every-frame equivalence verdict' with 'no actual frames' or 'no dynamic work ever': those are different statements.
- Public runtime and historical Sleepy backend evidence remain separate. A new size-support packet only supports the actually measured native configurations/world/source and cannot be extended to unmeasured controls or dynamic behavior.

## Source identities

SHA-256 identities are appended by the audit author after the read-only check.

Reviewed at 2026-11-14T15:10:05.800905+00:00.

| File | SHA-256 |
| --- | --- |
| `/Users/kerrylee/Documents/Codex/2026-11-10/1-sleepy-2-26-3-1/GOAL.md` | `08f44489225049f15a088e7765e73843b5aaaa882d3e4acd518541158e3c1f9c` |
| `/Users/kerrylee/Documents/Codex/2026-11-10/1-sleepy-2-26-3-1/artifacts/glass-noise-20261114/next-stage-dynamic-controlled-shapes-protocol.md` | `67f17fff70256b0691dbfca0a6eb3018ac9b299adb4523f09d5f219e91441cbb` |
| `/Users/kerrylee/Documents/Codex/2026-11-10/1-sleepy-2-26-3-1/artifacts/glass-noise-20261114/next-stage-dynamic-controlled-shapes-protocol.json` | `f90a0458b1015458c843008e020fef50f207c11d6082c955766fb408ef3ffe32` |
| `/Users/kerrylee/Documents/Codex/sleepy-liquid-glass/README.md` | `db9b478f2ad5e4ed9fbe1260f3d92189e2494461ce312a1ced36fdcfbeb494b9` |
| `/Users/kerrylee/Documents/Codex/sleepy-liquid-glass/README.en.md` | `ba0be2f8bd6705baaff8a5f808d2433980d596cd575130ff4c599f91ca0ca2a1` |
| `/Users/kerrylee/Documents/Codex/sleepy-liquid-glass/VALIDATION.md` | `9970a727fd7a865522a0e1c210dc8a846504a43819016bdd3b51f1c5ac4ddf15` |
