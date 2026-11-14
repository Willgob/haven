# haven

A two-player relay-shot prototype built with pygame: one projectile, two players.

## How it plays

- **Player A** (blue cannon, left) aims with the mouse and fires with `SPACE` or left click.
- Somewhere mid-field sits the **relay marker**. When the projectile reaches it, time
  slows down and **Player B** (orange cannon, right) takes over with ONE action:
  - a single angle **nudge** — `LEFT`/`RIGHT` arrows or `A`/`D` (±14°), or
  - a **bumper** — left click to drop one ahead of the ball; it reflects the shot.
- The handoff window lasts 3 real seconds; take no action and control closes for good.
- The shot only counts when it lands in B's catch ring. The marker is re-rolled every
  round, so call your shots and pass the projectile between you.

Run with `python main.py` (see `requirements.txt`).

## Tuning knobs

All the feel of the mechanic lives in the constants at the top of `main.py`:
ball speed, relay radius, handoff window, slow-mo scale, nudge angle, bumper
size, and catch radius.
