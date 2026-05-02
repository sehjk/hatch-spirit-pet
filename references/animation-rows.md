# Animation Rows

The Codex app reads one fixed atlas: 8 columns, 9 rows, 192x208 pixels per cell.

| Row | State | Generic spirit meaning | Fighter-compatible meaning | Used columns | Durations |
| --- | --- | --- | --- | ---: | --- |
| 0 | idle | signature idle / breathing / hover | combat stance / breathing guard | 0-5 | 280, 110, 110, 140, 140, 320 ms |
| 1 | running-right | travel right / glide / scamper / dash | dash right | 0-7 | 120 ms each, final 220 ms |
| 2 | running-left | travel left / glide / scamper / dash | dash left | 0-7 | 120 ms each, final 220 ms |
| 3 | waving | greeting / flourish / charm / ritual | taunt / stance flourish | 0-3 | 140 ms each, final 280 ms |
| 4 | jumping | hop / float / leap / transformation beat | leap / aerial pose | 0-4 | 140 ms each, final 280 ms |
| 5 | failed | startled / sad / dispelled / tired | hit-stun, KO, or defeated | 0-7 | 140 ms each, final 240 ms |
| 6 | waiting | anticipation / charge / listening / ambient loop | charge-up / power idle | 0-5 | 150 ms each, final 260 ms |
| 7 | running | active work loop / hurry / patrol / pursuit | forward rush loop | 0-5 | 120 ms each, final 220 ms |
| 8 | review | special moment / reveal / spell / celebration | special power / finisher loop | 0-5 | 150 ms each, final 280 ms |

Unused cells after each row's final used column must be fully transparent.

## Row Purposes

- `idle`: signature idle; breathing, hover, blink, guard, shimmer, pulse, or slight weight shift.
- `running-right`: travel to the right; 8-frame loop should read directionally.
- `running-left`: travel to the left; mirror only when asymmetric costume, prop, markings, or effects remain acceptable.
- `waving`: greeting, charm, flourish, ritual, taunt, or stance change; clear start, gesture, return.
- `jumping`: hop, float, leap, pop-up, aerial pose, or transformation beat; anticipation, lift, peak, descent, settle.
- `failed`: startled, sad, dispelled, tired, knocked back, or defeated reaction; readable but not visually noisy.
- `waiting`: anticipation, charge, listening, thinking, ambient power, or quiet readiness loop.
- `running`: active work loop, hurry, patrol, pursuit, forward rush, or in-place motion loop.
- `review`: special moment, reveal, spell, flourish, celebration, finisher, or power loop; attached effects are allowed when contained inside each frame slot.
