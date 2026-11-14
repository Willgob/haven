# haven

**BOUNCE BACK – Pixel Arcade** — a two-player retro arcade shooter built with
pygame (pygame-ce). One shared arena, one bouncing target, 60 seconds on the clock.

## The game

Both players gun for the same energy core bouncing around the middle of the
arena. It never stops moving: it ricochets off the boundaries, gets smaller and
faster as the match progresses, and bounces back hard every time it's hit.
Smaller targets score more — the tiny end-game core is worth 10 points a hit.
**Banked shots pay double or triple**: a bullet that ricochets off a wall
before it hits multiplies the tier — one bounce scores ×2 ("BANK SHOT!"), two
bounces ×3 ("DOUBLE BANK!"). Missed shots ricochet off the back wall and come
back around, so keep trying.

### Winning

The player with the most points when the clock hits zero takes the match — a
live `>` / `<` marker in the HUD shows who is ahead at a glance. If the scores
are tied at 0:00, **SUDDEN DEATH** kicks in: the timer stops, the arena keeps
running, and the first point scored wins the match, so there is always a
winner. Results of sudden-death matches are tagged "SETTLED IN SUDDEN DEATH!".

## Game modes

- **1P – VS CPU** — you (blue) against a computer gunner (orange). The CPU leads
  the target's motion but its aim wanders and gets sloppier as the match heats up.
- **2P – VERSUS** — two players share the keyboard.

Pick a mode from the main menu (click a button, or press `1` / `2`).

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

## Screens & sound

Main menu (title, mode select, instructions) → 60-second match (shared arena,
live scoreboard, countdown timer, target-difficulty readout, encouraging
banners) → results (winner announcement, final scores, confetti, proper draw
handling) — plus a pause overlay, all rendered in one shared arena with no
split screen.

The soundtrack is procedural chiptune, generated in code at startup (no audio
files): a bouncy menu loop, a driving gameplay loop that switches to a
double-time "hurry" variant in the final 10 seconds, a low-pass muffled mix
while paused, and a calm victory loop on the results screen. Sound effects are
synthesized square/noise blips, plus cartoon-spring "boing" waves that fire
every time a bullet ricochets or the target gets knocked back.

The arena itself is rubber: stitched bumper walls with gold spring pads in the
corners, and every impact — bullet ricochet or target hit — sends an expanding
ripple ring through the wall.

## Tech notes

- The whole game renders to a 320×180 virtual screen scaled ×4 with
  nearest-neighbour blitting — sprites, text and effects are genuinely
  pixelated, not just smooth graphics with pixel-style text.
- All pixel art is procedural (character maps and drawing routines baked once
  at startup), text uses a hand-built 3×5 bitmap font, and music and sound
  effects are synthesized in code — no asset files, no extra dependencies.
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
cooldowns, scoring tiers, the CPU opponent's skill (`CPU_*`) and the
encouragement messages all live at the top of `settings.py`. Music tempo,
patterns and mix volumes are in `music.py`.
