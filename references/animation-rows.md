# Animation Rows

The Codex app reads one fixed atlas: 8 columns, 9 rows, 192x208 pixels per cell. The rows are stable technical slots; `prepare_pet_run.py` maps them to concrete animation actions from the selected action preset, then applies any `--state-action state=value` overrides.

| Row | State | Default generic slot | Used columns | Durations |
| --- | --- | --- | ---: | --- |
| 0 | idle | signature idle / breathing / hover | 0-5 | 280, 110, 110, 140, 140, 320 ms |
| 1 | running-right | travel right / glide / scamper / dash | 0-7 | 120 ms each, final 220 ms |
| 2 | running-left | travel left / glide / scamper / dash | 0-7 | 120 ms each, final 220 ms |
| 3 | waving | greeting / flourish / charm / ritual | 0-3 | 140 ms each, final 280 ms |
| 4 | jumping | hop / float / leap / transformation beat | 0-4 | 140 ms each, final 280 ms |
| 5 | failed | startled / sad / dispelled / tired | 0-7 | 140 ms each, final 240 ms |
| 6 | waiting | anticipation / charge / listening / ambient loop | 0-5 | 150 ms each, final 260 ms |
| 7 | running | active work loop / hurry / patrol / pursuit | 0-5 | 120 ms each, final 220 ms |
| 8 | review | special moment / reveal / spell / celebration | 0-5 | 150 ms each, final 280 ms |

Unused cells after each row's final used column must be fully transparent.

## Row Purpose Compilation

- `--action-style` supplies concrete purposes for all nine states.
- `--state-action state=value` replaces the preset purpose for one state.
- `--action-notes` adds global action guidance without replacing the per-state purpose.
- Directional rows must still read as left/right motion regardless of action preset.
- `running-left` may be mirrored from `running-right` only when asymmetric costume, prop, markings, or effects remain acceptable.
- Attached effects are allowed when contained inside each frame slot and consistent with the selected art style.
