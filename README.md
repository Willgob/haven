# Haven Sydney Project

## BOUNCE BACK

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

Shots can earn bonus points too. Every wall bounce a bullet banks off raises
its multiplier: one bounce pays double (BANK SHOT!), three bounces pay x5
(TRIPLE BANK!). The jackpot is the title shot - a bullet that ricochets all
the way off your own back wall and heads back out pays x6 (BOUNCE BACK!).
Each wall bounce also refunds a little bullet lifetime, so banked shots can
fly much farther than straight ones, and they visibly heat up with a trail
as their multiplier grows. A hit landed just after the core bounces off an
arena wall earns an extra REBOUND! bonus worth its base points.

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
