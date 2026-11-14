"""Players, bullets, the target and the little effects."""

import math
import random

import pygame

from settings import (
    ARENA_L, ARENA_R, BOUNCE_LIFE_BONUS, BULLET_LIFETIME, BULLET_MAX_BOUNCES,
    BULLET_SPEED, BULLET_Y_OFFSET, CONTROLS, CPU_AIM_ERROR, CPU_COOLDOWN,
    CPU_FIRE_WINDOW, CPU_LAPSE, CPU_LEAD, GUN_LEN, MUZZLE_DIST, PLAY_BOTTOM,
    PLAY_TOP, PLAYER_SPEED, POP_LIFE, REBOUND_WINDOW, RIPPLE_TTL,
    SHOT_COOLDOWN, TARGET_DARK, BULLET_CAP, UI_LINE, UI_MID, TARGET_BODY,
    TARGET_LIGHT, TARGET_CORE, tier_for_size, P1_COLORS, P2_COLORS,
)
from pixel_font import draw_text

_TRAIL_KEEP = 6              # trail samples kept for hot banked bullets


def clamp(value, lo, hi):
    return lo if value < lo else hi if value > hi else value


def point_seg_dist(px, py, ax, ay, bx, by):
    """Distance from point (px, py) to segment (ax, ay)-(bx, by)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


class Player:
    """A gunner on one side of the arena. Moves vertically, fires horizontally."""

    def __init__(self, pid, x, y, assets, is_cpu=False):
        self.pid = pid
        self.face = 1 if pid == "p1" else -1
        self.assets = assets["players"][pid]
        self.colors = self.assets["colors"]
        self.x = float(x)
        self.y = float(y)
        self.score = 0
        self.cooldown = 0.0
        self.recoil = 0.0
        self.anim = 0.0
        self.moving = False
        self.is_cpu = is_cpu
        self.aim_error = 0.0
        self.aim_t = 0.0

    def muzzle(self):
        return (self.x + self.face * MUZZLE_DIST, self.y + BULLET_Y_OFFSET)

    def fire(self, match):
        if self.cooldown > 0.0 or len(match.bullets) >= BULLET_CAP:
            return
        self.cooldown = CPU_COOLDOWN if self.is_cpu else SHOT_COOLDOWN
        self.recoil = 0.1
        match.spawn_bullet(self)

    def update(self, dt, held, match):
        up_key, down_key, shoot_key = CONTROLS[self.pid]
        vy = 0.0
        if held(up_key):
            vy -= 1.0
        if held(down_key):
            vy += 1.0
        self.moving = vy != 0.0
        self.y += vy * PLAYER_SPEED * dt
        self.y = clamp(self.y, PLAY_TOP + 7, PLAY_BOTTOM - 7)
        self.cooldown = max(0.0, self.cooldown - dt)
        self.recoil = max(0.0, self.recoil - dt)
        self.anim += dt * (10.0 if self.moving else 3.0)
        if held(shoot_key):
            self.fire(match)

    def update_cpu(self, dt, match):
        """1P opponent: aims where the target will be, badly."""
        target = match.target
        dx = max(30.0, abs(target.x - self.x))
        travel = dx / BULLET_SPEED
        predict_y = target.y + target.vy * travel * CPU_LEAD + self.aim_error
        diff = predict_y - self.y
        if abs(diff) > 1.5:
            self.y += clamp(diff, -1.0, 1.0) * PLAYER_SPEED * dt
            self.moving = True
        else:
            self.moving = False
        self.y = clamp(self.y, PLAY_TOP + 7, PLAY_BOTTOM - 7)
        self.aim_t -= dt
        if self.aim_t <= 0.0:
            self.aim_t = random.uniform(0.35, 0.9)
            # aim gets sloppier as the match goes on
            pressure = 1.0 + match.elapsed / 40.0
            if random.random() < CPU_LAPSE:
                span = CPU_AIM_ERROR * 3 * pressure
            else:
                span = CPU_AIM_ERROR * pressure
            self.aim_error = random.uniform(-span, span)
        self.cooldown = max(0.0, self.cooldown - dt)
        self.recoil = max(0.0, self.recoil - dt)
        self.anim += dt * (10.0 if self.moving else 3.0)
        if abs(predict_y - self.y) <= CPU_FIRE_WINDOW:
            self.fire(match)

    def draw(self, surf, t, dx=0, dy=0):
        blink_on = int(t * 3.0) % 2 == 0
        frames = self.assets["frames"] if blink_on else self.assets["frames_off"]
        frame = frames[int(self.anim) % 2]
        bob = 1 if (not self.moving and int(t * 2.0) % 2) else 0
        shift = self.face if self.recoil > 0 else 0
        px = int(round(self.x)) - 5 + dx - shift
        py = int(round(self.y)) - 6 + dy - bob
        surf.blit(frame, (px, py))
        # gun
        gx = int(round(self.x)) - shift
        gy = int(round(self.y)) + 1 + dy
        x_edge = gx + self.face * 4
        left = x_edge if self.face > 0 else x_edge - GUN_LEN
        pygame.draw.rect(surf, self.colors["metal"], (left, gy, GUN_LEN, 2))
        tip_x = gx + self.face * (4 + GUN_LEN - 1)
        pygame.draw.rect(surf, self.colors["light"], (tip_x, gy, 1, 2))
        # muzzle flash
        if self.recoil > 0.045:
            if self.recoil > 0.075:
                flash, off = self.assets["flash_big"], 2
            else:
                flash, off = self.assets["flash_small"], 1
            mx, my = self.muzzle()
            surf.blit(flash, (int(mx) - off, int(my) - 1))


class Bullet:
    """A pixel bolt that flies across the arena and ricochets off the walls.

    Every wall bounce refunds a little lifetime and raises the bank
    multiplier. A bullet that touches its shooter's back wall and heads back
    out again carries the BOUNCE BACK jackpot on its next hit.
    """

    def __init__(self, owner, x, y, face):
        self.owner = owner
        self.face = face
        self.px = float(x)
        self.py = float(y)
        self.x = float(x)
        self.y = float(y)
        self.vx = face * BULLET_SPEED
        self.alive = True
        self.anim = 0.0
        self.life = 0.0
        self.bounces = 0
        self.backed = False     # touched the shooter's back wall
        self.trail = []         # recent positions, for the hot-bullet trail

    def update(self, dt):
        self.px, self.py = self.x, self.y
        self.anim += dt
        self.life += dt
        self.x += self.vx * dt
        if self.x <= ARENA_L + 1:
            self.x = ARENA_L + 1
            self.vx = abs(self.vx)
            self.bounces += 1
            self.backed = self.face > 0      # left wall is p1's back wall
            return self._end_or_bounce()
        if self.x >= ARENA_R - 1:
            self.x = ARENA_R - 1
            self.vx = -abs(self.vx)
            self.bounces += 1
            self.backed = self.face < 0      # right wall is p2's back wall
            return self._end_or_bounce()
        if self.life > BULLET_LIFETIME:
            self.alive = False
            return "fizzle"
        self.trail.append((self.x, self.y))
        if len(self.trail) > _TRAIL_KEEP:
            self.trail.pop(0)
        return None

    def _end_or_bounce(self):
        self.life -= BOUNCE_LIFE_BONUS       # the bounce keeps it alive
        if self.bounces > BULLET_MAX_BOUNCES:
            self.alive = False
        return "wall"

    def draw(self, surf, bundle, dx=0, dy=0):
        tier = min(self.bounces, 2)          # 0 normal, 1 hot, 2+ super
        if tier and self.trail:
            ramp = bundle["ramp"]
            step = max(1, len(self.trail) // 3)
            for i, (tx, ty) in enumerate(self.trail[::step][-3:]):
                surf.fill(ramp[min(i, 2)], (int(tx) + dx, int(ty) + dy, 1, 1))
        if tier == 0:
            frames = bundle["frames"]
        elif tier == 1:
            frames = bundle["hot"]
        else:
            frames = bundle["super"]
        frame = frames[int(self.anim * 22) % 2]
        surf.blit(frame, (int(self.x) - 2 + dx, int(self.y) - 1 + dy))


class Target:
    """The bouncing core both players shoot at."""

    def __init__(self, zone, size_fn, speed_fn, sfx=None, target_frames=None):
        self.zone = zone
        self.size_fn = size_fn
        self.speed_fn = speed_fn
        self.sfx = sfx
        self.frames_by_size = target_frames
        self.x = float(zone.centerx)
        self.y = float(zone.centery)
        self.size = size_fn(0.0)
        self.base_speed = speed_fn(0.0)
        angle = random.uniform(0.0, math.tau)
        self.vx = math.cos(angle) * self.base_speed
        self.vy = math.sin(angle) * self.base_speed
        self.flash = 0.0
        self.boost = 0.0
        self.rebound = 0.0     # time left in the "just bounced off a wall" window
        self.impulse_t = random.uniform(2.5, 5.5)

    def radius(self):
        return max(2.0, self.size / 2.0)

    def _rotate(self, angle):
        c, s = math.cos(angle), math.sin(angle)
        self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c

    def update(self, dt, elapsed):
        self.size = self.size_fn(elapsed)
        self.base_speed = self.speed_fn(elapsed)
        self.boost = max(0.0, self.boost - dt)
        self.flash = max(0.0, self.flash - dt)
        self.rebound = max(0.0, self.rebound - dt)
        speed = self.base_speed * (1.0 + 0.6 * self.boost)
        current = math.hypot(self.vx, self.vy)
        if current < 1e-6:
            self.vx, self.vy = speed, 0.0
        else:
            factor = speed / current
            self.vx *= factor
            self.vy *= factor
        self.x += self.vx * dt
        self.y += self.vy * dt

        zone = self.zone
        radius = self.radius()
        bounced = False
        if self.x - radius < zone.left:
            self.x = zone.left + radius
            self.vx = abs(self.vx)
            bounced = True
        elif self.x + radius > zone.right:
            self.x = zone.right - radius
            self.vx = -abs(self.vx)
            bounced = True
        if self.y - radius < zone.top:
            self.y = zone.top + radius
            self.vy = abs(self.vy)
            bounced = True
        elif self.y + radius > zone.bottom:
            self.y = zone.bottom - radius
            self.vy = -abs(self.vy)
            bounced = True
        if bounced:
            self._rotate(random.uniform(-0.14, 0.14))
            self.rebound = REBOUND_WINDOW
            if self.sfx:
                self.sfx.play("bounce")
        self.impulse_t -= dt
        if self.impulse_t <= 0.0:
            self.impulse_t = random.uniform(2.5, 5.5)
            self._rotate(random.uniform(-0.6, 0.6))

    def hit(self, bullet_x):
        """Bounce away from the shot, return the points."""
        points, label, color = tier_for_size(self.size)
        away = 1.0 if self.x >= bullet_x else -1.0
        speed = self.base_speed
        self.vx = away * speed * 0.85
        self.vy = clamp(self.vy, -speed * 0.5, speed * 0.5)
        self.flash = 0.09
        self.boost = 1.0
        return points, label, color

    def draw(self, surf, t, dx=0, dy=0):
        size = int(round(self.size))
        size = max(4, min(18, size))
        bundle = self.frames_by_size[size]
        frame_idx = int(t * 9.0) % 4
        if self.flash > 0.0:
            frame = bundle["white"][int(t * 30.0) % 4]
        else:
            frame = bundle["frames"][frame_idx]
        ox = int(round(self.x)) - (size // 2 + 2) + dx
        oy = int(round(self.y)) - (size // 2 + 2) + dy
        surf.blit(frame, (ox, oy))
        if size >= 8 and self.flash <= 0.0:
            # pupil looks where it's headed
            speed = math.hypot(self.vx, self.vy) or 1.0
            px = int(round(self.x + self.vx / speed * size * 0.18))
            py = int(round(self.y + self.vy / speed * size * 0.18))
            pygame.draw.rect(surf, TARGET_DARK, (px + dx, py + dy, 2, 2))


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "colors", "size")

    def __init__(self, x, y, vx, vy, life, colors, size=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.colors = colors
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        damp = math.pow(0.3, dt)
        self.vx *= damp
        self.vy *= damp
        self.life -= dt
        return self.life > 0.0

    def draw(self, surf, dx=0, dy=0):
        frac = max(0.0, self.life / self.max_life)
        color = self.colors[0] if frac > 0.45 else self.colors[1]
        pygame.draw.rect(surf, color, (int(self.x) + dx, int(self.y) + dy, self.size, self.size))


class ScorePop:
    """Floating '+5' that drifts up and blinks out."""

    def __init__(self, x, y, text, color):
        self.x = x
        self.y0 = y
        self.text = text
        self.color = color
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        return self.t < POP_LIFE

    def draw(self, surf, dx=0, dy=0):
        if self.t > POP_LIFE * 0.6 and int(self.t * 20) % 2 == 0:
            return
        y = self.y0 - self.t * 16
        draw_text(surf, self.text, (self.x + dx, y + dy), self.color, 1, "center")


class Ripple:
    """Impact ring on the rubber walls."""

    __slots__ = ("x", "y", "life", "max_life", "colors")

    def __init__(self, x, y, colors, life=RIPPLE_TTL):
        self.x = x
        self.y = y
        self.life = life
        self.max_life = life
        self.colors = colors

    def update(self, dt):
        self.life -= dt
        return self.life > 0.0

    def draw(self, surf, dx=0, dy=0):
        frac = self.life / self.max_life
        color = self.colors[0] if frac > 0.5 else self.colors[1]
        cx, cy = int(self.x) + dx, int(self.y) + dy
        radius = max(1, int(2.0 + (1.0 - frac) * 7.0))   # grows as it fades
        points = ((cx + radius, cy), (cx, cy + radius),
                  (cx - radius, cy), (cx, cy - radius))
        pygame.draw.polygon(surf, color, points, 1)
