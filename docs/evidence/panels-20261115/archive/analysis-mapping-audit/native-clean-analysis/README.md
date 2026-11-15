# Clean native panel feasibility audit

This audit is frozen before decoding the new clean fixture. It covers only the two selected calibration inputs, light appearance, and native system Alert/Sheet in four separate r2 launches. The earlier failed capture and old backing condition remain separate.

Execution requires the root agent to hand off the complete successful r2 capture. Then run `analyze.py --execute-after-root-handoff` using the Python runtime that provides NumPy and Pillow. The script is not run by preparing these files.

Before any image decode, the audit binds the capture plan, binary freeze, execution receipts, all 16 PNG/16 AX attachments, four session traces, and the two unchanged source files by SHA256. Source identity, full 375×667pt @2 world mapping, native OS and traits, request/capture/AX chronology, hidden trigger absence, delivered title touch and relay, public controller geometry, and AX foreground geometry are recorded separately.

REST stability requires strict zero RGBA difference across the entire 750×1334 screenshot on both raw and embedded-profile-normalized sRGB tracks. No crop, mask, channel tolerance, recenter, registration or warp can rescue a nonzero result. Missing embedded profiles fail the normalized-track availability gate.

Source exactness uses the fixed rectangles in analysis-plan.json: Alert and Sheet source cores, fixed 2/8/24/60pt stress collars, the retained S07 support, and all three old backing-trigger rectangles. Pixel-center membership is evaluated in the original fixed canvas. The 60pt collar is a stress test, not a measured upper bound on native blur support. Whole-image before/after and source differences are also reported independently, including system chrome; they are never replaced by cropped context comparisons.

This is a feasibility check, not an optical parity claim. Public controller/AX agreement does not prove a material contour, central contour/tangent invariance, native blur kernel support, a unique source map, refraction or physical thickness. The clean condition cannot be silently pooled with old polluted optical pixels. All failures are retained without post-hoc threshold or ROI fallbacks.
