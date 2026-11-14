# Haven Sydney Project

## BO U NCE BACK

**BOUNCE BACK** is a two-player retro arcade shooter made with pygame-ce.
You share an arena, chase one bouncing energy core, and have 60 seconds to
score as many points as possible.

## How it works

The energy core is always moving. It ricochets around the arena, becoming
smaller and faster as the match goes on. Every time someone hits it, it gets
knocked back with a satisfying bounce.

The smaller the core, the more it is worth:

| Target size | Points |
| ----------- | ------ |
| Large       | 1      |
| Medium      | 3      |
| Small       | 5      |
| Tiny        | 10     |

Shots can earn bonus points too. A bullet that bounces off a wall before
hitting the core is a bank shot and scores double. Two wall bounces score
triple. Missed shots keep ricocheting around the arena, so a shot that looks
lost may still come back and save the day.

## Winning

When the timer reaches zero, the player with the highest score wins. A `>` or
`<` marker in the HUD shows who is currently ahead.

If the score is tied at the end of the match, the game goes into **SUDDEN
DEATH**. The timer stops, the arena keeps moving, and the next point wins.
That way, every match has a winner.

## Game modes

- **1P – VS CPU** — Play as the blue gunner against an orange computer
  opponent. The CPU predicts where the core is going, but its aim gets less
  reliable as the match gets more intense.
- **2P – VERSUS** — Two players compete on the same keyboard.

Choose a mode from the main menu by clicking a button or pressing `1` or `2`.

## Controls

| Action | Player 1 (blue, left) | Player 2 (orange, right) |
| ------ | --------------------- | ------------------------ |
| Move   | W / S                 | UP / DOWN                |
| Shoot  | SPACE (hold to fire)  | ENTER (hold to fire)     |

- `ESC` / `P` — Pause the match. The game also pauses when the window loses
  focus.
- Pause menu — Choose **RESUME**, **RESTART**, or **MAIN MENU** with
  `ESC` / `R` / `M`, or click an option.
- Results screen — Choose **PLAY AGAIN** or **MAIN MENU** with `ENTER` /
  `ESC`, or click an option.

## Screens and sound

The game flows from the main menu to a 60-second match and then to a results
screen. You will see the mode select, instructions, live scoreboard, timer,
target difficulty, winner announcement, final scores, confetti, and proper
draw handling. There is also a pause overlay, all inside one shared arena.

The soundtrack is generated in code, so there are no audio files to download.
The menu has a light chiptune loop, gameplay has a faster version for the last
10 seconds, pausing applies a muffled effect, and the results screen has a
calmer victory tune. Ricochets and target hits get their own square-wave,
noise, and cartoon spring sound effects.

The arena is designed to feel like a giant rubber bumper. It has stitched
walls, gold spring pads in the corners, and a ripple effect whenever a bullet
or the core hits a boundary.

## Tech notes

- The game draws to a 320×180 virtual screen and scales it up by 4 using
  nearest-neighbour scaling. Everything stays intentionally pixelated.
- Pixel art, text, music, and sound effects are generated in code. There are
  no asset files and no extra dependencies beyond pygame-ce.
- Movement uses delta time with a safety clamp, and swept circle-to-segment
  collision checks stop fast bullets from passing through the core.

## Run it

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## Tuning

The main gameplay settings are collected at the top of `settings.py`. This is
where you can change the match length, core size and speed curve, bullet speed,
ricochet rules, cooldowns, scoring tiers, CPU skill (`CPU_*`), and the
encouragement messages.

Music tempo, patterns, and volume settings live in `music.py`.
