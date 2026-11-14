# haven

**BOUNCE BACK – Pixel Arcade** — a two-player retro arcade shooter built with
pygame (pygame-ce). One shared arena, one bouncing target, 60 seconds on the clock.

## The game

Both players gun for the same energy core bouncing around the middle of the
arena. It never stops moving: it ricochets off the boundaries, gets smaller and
faster as the match progresses, and bounces back hard every time it's hit.
Smaller targets score more — the tiny end-game core is worth 10 points a hit.
Highest score when the timer hits zero wins. Missed shots ricochet off the back
wall and come back around, so keep trying.

| Target size | Points |
| ----------- | ------ |
| Large       | 1      |
| Medium      | 3      |
| Small       | 5      |
| Tiny        | 10     |

## Controls (shared keyboard)

| Action | Player 1 (blue, left)      | Player 2 (orange, right)     |
| ------ | -------------------------- | ---------------------------- |
| Move   | W / S                      | UP / DOWN                    |
| Shoot  | SPACE (hold to auto-fire)  | ENTER (hold to auto-fire)    |

- `ESC` / `P` — pause (the match also auto-pauses if the window loses focus)
- Pause menu: RESUME · RESTART · MAIN MENU (ESC / R / M, or mouse)
- Results: PLAY AGAIN · MAIN MENU (ENTER / ESC, or mouse)

## Screens

Main menu (title, play button, instructions) → 60-second match (shared arena,
live scoreboard, countdown timer, target-difficulty readout, encouraging
banners) → results (winner announcement, final scores, confetti, proper draw
handling) — plus a pause overlay, all rendered in one shared arena with no
split screen.

## Tech notes

- The whole game renders to a 320×180 virtual screen scaled ×4 with
  nearest-neighbour blitting — sprites, text and effects are genuinely
  pixelated, not just smooth graphics with pixel-style text.
- All pixel art is procedural (character maps and drawing routines baked once
  at startup), text uses a hand-built 3×5 bitmap font, and sound effects are
  synthesized square/noise waves — no asset files, no extra dependencies.
- Frame-rate independent movement (delta time with a safety clamp) and swept
  circle-vs-segment collisions so fast bullets never tunnel through the target.

## Run

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # pygame-ce only
.venv/bin/python main.py
```

## Tuning

Match length, the target size/speed curve, bullet speed and ricochet rules,
cooldowns, scoring tiers and the encouragement messages all live at the top of
`settings.py`.
