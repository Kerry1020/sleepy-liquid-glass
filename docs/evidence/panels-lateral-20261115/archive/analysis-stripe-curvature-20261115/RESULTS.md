# Fixed light Alert apparent-color diagnostic

Only the frozen four boundaries were analyzed. Raw and normalized-sRGB tracks are identical by explicit PNG sRGB provenance. Screen and Window remain separate. This is historical calibration and does not identify unique2Dmap, physical thickness or native equivalence.

| image | source boundary | eligible / 344 | center reference | top24 outward median [pt] | bottom24 outward median [pt] |
|---|---:|---:|---:|---:|---:|
| native | 54 | 40 | 53.7866 | 0.8870 | 0.7470 |
| native | 324 | 62 | 324.0777 | 0.3111 | -0.0779 |
| native | 72 | 16 | unavailable | unavailable | unavailable |
| native | 306 | 9 | unavailable | unavailable | unavailable |
| android_screen | 54 | 9 | unavailable | unavailable | unavailable |
| android_screen | 324 | 16 | unavailable | unavailable | unavailable |
| android_screen | 72 | 5 | unavailable | unavailable | unavailable |
| android_screen | 306 | 61 | 306.0374 | 0.0000 | 0.2477 |
| android_window | 54 | 3 | unavailable | unavailable | unavailable |
| android_window | 324 | 0 | unavailable | unavailable | unavailable |
| android_window | 72 | 5 | unavailable | unavailable | unavailable |
| android_window | 306 | 61 | 306.0374 | 0.0000 | 0.2413 |

Failed rows stay failed. `rows.jsonl.gz` retains RGB/alpha, all 10/50/90 up/down/tie branches, peak structure and exact failed gates. `contours.csv` contains x(y), center differences and h=4pt slope/angle/curvature only on complete contiguous eligible support. `analysis.json` contains every support and paired difference; no favorable branch or center segment is substituted.

Foreground masks jointly exclude native AX and actual Android front slots (+2pt). In particular y363.5–415.5 is occluded at these supports; no derivative crosses it. Native underlying source buttons remain historical context, not reclassified as front masks.

`small-original-comparison.png` is two exact 640×344 integer crops. `apparent-contours.png` shows eligible contiguous curves; faint points preserve every failed 50% branch and are not measurements accepted by the gate.
