# Relay Shot - one projectile, two players.
#
# Player A (left) aims and fires. Mid-field sits the relay marker: when the
# projectile reaches it, time slows and Player B (right) takes over with ONE
# action - a single angle nudge (LEFT/RIGHT or A/D) or a bumper (click to
# place). The shot only counts when it lands in B's catch ring, so aim it,
# call it, and pass it between you.

import math
import random

import pygame

WIDTH, HEIGHT = 1280, 720
FPS = 60
WALL = 8

BALL_SPEED = 500.0
BALL_RADIUS = 7.0
BALL_LIFETIME = 12.0        # sim seconds before a shot is called dead
TRAIL_LEN = 34

RELAY_RADIUS = 64.0         # pass this close to the marker to hand off
RELAY_WINDOW = 3.0          # real seconds Player B has, in slow motion
RELAY_SLOWMO = 0.25
NUDGE_ANGLE = 14.0          # degrees, Player B's single nudge

BUMPER_RADIUS = 26.0
BUMPER_MIN_DIST = 46.0      # can't drop a bumper right on the ball

CATCH_RADIUS = 74.0         # Player B's catch ring

A_POS = pygame.math.Vector2(96, HEIGHT * 0.5)
B_POS = pygame.math.Vector2(WIDTH - 96, HEIGHT * 0.5)

COLOR_BG = (13, 13, 18)
COLOR_WALL = (38, 38, 52)
COLOR_A = (86, 178, 233)
COLOR_B = (244, 166, 60)
COLOR_BALL = (245, 245, 245)
COLOR_RELAY = (232, 84, 122)
COLOR_TEXT = (235, 235, 235)
COLOR_DIM = (108, 108, 128)
COLOR_OK = (118, 216, 140)
COLOR_TRAIL = (150, 150, 160)


def pt(v):
    return (round(v.x), round(v.y))


def lerp_color(c0, c1, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))


def draw_dashed_line(screen, start, end, color, width=2, dash=14, gap=10):
    delta = end - start
    length = delta.length()
    if length < 1:
        return
    step = delta / length
    t = 0.0
    while t < length:
        a = start + step * t
        b = start + step * min(t + dash, length)
        pygame.draw.line(screen, color, pt(a), pt(b), width)
        t += dash + gap


def draw_dashed_circle(screen, center, radius, color, width=2, dashes=24, skip=0.35):
    span = (math.tau / dashes) * (1.0 - skip)
    for i in range(dashes):
        a0 = (i / dashes) * math.tau
        p0 = center + pygame.math.Vector2(math.cos(a0), math.sin(a0)) * radius
        p1 = center + pygame.math.Vector2(math.cos(a0 + span), math.sin(a0 + span)) * radius
        pygame.draw.line(screen, color, pt(p0), pt(p1), width)


def blit_text(screen, font, string, pos, color, anchor="topleft"):
    surf = font.render(string, True, color)
    rect = surf.get_rect(**{anchor: (round(pos[0]), round(pos[1]))})
    screen.blit(surf, rect)


def first_wall_hit(pos, direction):
    """Where a ray from pos going 'direction' first meets the arena wall."""
    left = WALL + BALL_RADIUS
    right = WIDTH - WALL - BALL_RADIUS
    top = WALL + BALL_RADIUS
    bottom = HEIGHT - WALL - BALL_RADIUS
    tx = ty = math.inf
    if direction.x > 1e-6:
        tx = (right - pos.x) / direction.x
    elif direction.x < -1e-6:
        tx = (left - pos.x) / direction.x
    if direction.y > 1e-6:
        ty = (bottom - pos.y) / direction.y
    elif direction.y < -1e-6:
        ty = (top - pos.y) / direction.y
    t = max(min(tx, ty), 0.0)
    hit = pos + direction * t
    if tx < ty:
        reflected = pygame.math.Vector2(-direction.x, direction.y)
    else:
        reflected = pygame.math.Vector2(direction.x, -direction.y)
    return hit, reflected


class Ball:
    def __init__(self, pos, vel):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.trail = []
        self.life = 0.0


class RelayShot:
    def __init__(self, screen):
        self.screen = screen
        self.font_small = pygame.font.Font(None, 24)
        self.font_mid = pygame.font.Font(None, 32)
        self.font_big = pygame.font.Font(None, 62)
        self.state = "aim"          # aim | flight | result
        self.round = 1
        self.score = 0
        self.aim_dir = pygame.math.Vector2(1, 0)
        self.ball = None
        self._reset_relay()
        self._new_marker()

    def _reset_relay(self):
        self.marker = pygame.math.Vector2(WIDTH * 0.5, HEIGHT * 0.5)
        self.relay_triggered = False
        self.relay_active = False
        self.relay_timer = 0.0
        self.action_used = None     # None | "nudge" | "bumper"
        self.bumper = None
        self.result = None
        self.flash_text = ""
        self.flash_timer = 0.0

    def _new_marker(self):
        self.marker.update(random.uniform(WIDTH * 0.38, WIDTH * 0.62),
                           random.uniform(120, HEIGHT - 120))

    def next_round(self):
        self.round += 1
        self.state = "aim"
        self.ball = None
        self._reset_relay()
        self._new_marker()

    def fire(self):
        if self.state != "aim":
            return
        muzzle = A_POS + self.aim_dir * 34
        self.ball = Ball(muzzle, self.aim_dir * BALL_SPEED)
        self.state = "flight"

    def start_handoff(self):
        self.relay_active = True
        self.relay_timer = RELAY_WINDOW

    def end_handoff(self):
        self.relay_active = False

    def nudge(self, sign):
        if self.state != "flight" or not self.relay_active or self.action_used:
            return
        self.ball.vel = self.ball.vel.rotate(sign * NUDGE_ANGLE)
        self.action_used = "nudge"
        self.end_handoff()

    def place_bumper(self, pos):
        if self.state != "flight" or not self.relay_active or self.action_used:
            return
        spot = pygame.math.Vector2(pos)
        if spot.distance_to(self.ball.pos) < BUMPER_MIN_DIST:
            self.flash_text = "too close to the ball - drop it further ahead"
            self.flash_timer = 1.4
            return
        self.bumper = spot
        self.action_used = "bumper"
        self.end_handoff()

    def handle_event(self, event):
        """Return False when the game should quit."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key == pygame.K_SPACE:
                if self.state == "aim":
                    self.fire()
                elif self.state == "result":
                    self.next_round()
            elif self.state == "flight" and self.relay_active and not self.action_used:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.nudge(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.nudge(1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "aim":
                self.fire()
            elif self.state == "result":
                self.next_round()
            elif self.state == "flight" and self.relay_active and not self.action_used:
                self.place_bumper(event.pos)
        return True

    def update(self, dt):
        self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.state == "aim":
            mouse = pygame.math.Vector2(pygame.mouse.get_pos())
            delta = mouse - A_POS
            if delta.length() > 4:
                self.aim_dir = delta.normalize()
            return
        if self.state != "flight" or self.ball is None:
            return

        b = self.ball
        step = dt * (RELAY_SLOWMO if self.relay_active else 1.0)
        b.life += step
        b.pos += b.vel * step
        self._bounce_walls(b)

        if not self.relay_triggered and b.pos.distance_to(self.marker) < RELAY_RADIUS:
            self.relay_triggered = True
            self.start_handoff()
        if self.bumper is not None:
            self._bounce_bumper(b)

        if b.pos.distance_to(B_POS) < CATCH_RADIUS:
            self.relay_active = False
            self.state = "result"
            self.result = ("win", f"handoff: {self.action_used or 'none taken'}")
            self.score += 1
            return

        b.trail.append(pygame.math.Vector2(b.pos))
        if len(b.trail) > TRAIL_LEN:
            b.trail.pop(0)

        if b.life > BALL_LIFETIME:
            self.state = "result"
            if self.relay_triggered:
                self.result = ("miss", "the handoff came and went - try again")
            else:
                self.result = ("miss", "the marker was never touched - talk it through")
            return

        if self.relay_active:
            self.relay_timer -= dt
            if self.relay_timer <= 0:
                self.end_handoff()
                self.flash_text = "window closed - no handoff action"
                self.flash_timer = 1.6

    def _bounce_walls(self, b):
        lo_x = WALL + BALL_RADIUS
        hi_x = WIDTH - WALL - BALL_RADIUS
        if b.pos.x < lo_x:
            b.pos.x = lo_x
            b.vel.x = abs(b.vel.x)
        elif b.pos.x > hi_x:
            b.pos.x = hi_x
            b.vel.x = -abs(b.vel.x)
        lo_y = WALL + BALL_RADIUS
        hi_y = HEIGHT - WALL - BALL_RADIUS
        if b.pos.y < lo_y:
            b.pos.y = lo_y
            b.vel.y = abs(b.vel.y)
        elif b.pos.y > hi_y:
            b.pos.y = hi_y
            b.vel.y = -abs(b.vel.y)

    def _bounce_bumper(self, b):
        delta = b.pos - self.bumper
        dist = delta.length()
        min_dist = BUMPER_RADIUS + BALL_RADIUS
        if 0.0 < dist < min_dist:
            normal = delta / dist
            b.pos = self.bumper + normal * (min_dist + 0.5)
            b.vel -= normal * (2.0 * b.vel.dot(normal))

    # ------------------------------------------------------------------ draw

    def draw(self, t):
        s = self.screen
        s.fill(COLOR_BG)
        self._draw_arena(s)
        self._draw_between(s)
        self._draw_marker(s, t)
        if self.bumper is not None:
            pygame.draw.circle(s, COLOR_B, pt(self.bumper), int(BUMPER_RADIUS))
            pygame.draw.circle(s, COLOR_BG, pt(self.bumper), int(BUMPER_RADIUS) - 8, 2)
        if self.state == "aim":
            self._draw_aim(s)
        if self.ball is not None:
            self._draw_ball(s)
        self._draw_cannons(s)
        self._draw_hud(s)
        if self.flash_timer > 0:
            blit_text(s, self.font_small, self.flash_text, (WIDTH / 2, 132), COLOR_DIM, "midtop")
        if self.relay_active:
            self._draw_handoff(s)
        if self.state == "result":
            self._draw_result(s)

    def _draw_arena(self, s):
        pygame.draw.rect(s, COLOR_WALL, (0, 0, WIDTH, WALL))
        pygame.draw.rect(s, COLOR_WALL, (0, HEIGHT - WALL, WIDTH, WALL))
        pygame.draw.rect(s, COLOR_WALL, (0, 0, WALL, HEIGHT))
        pygame.draw.rect(s, COLOR_WALL, (WIDTH - WALL, 0, WALL, HEIGHT))

    def _draw_between(self, s):
        """Faint dotted line marking the space the shot travels between."""
        steps = 24
        for i in range(1, steps):
            p = A_POS.lerp(B_POS, i / steps)
            pygame.draw.circle(s, (36, 36, 50), pt(p), 2)

    def _draw_marker(self, s, t):
        pulse = 0.5 + 0.5 * math.sin(t * 3.2)
        ring_color = (96, 96, 112) if self.relay_triggered else COLOR_RELAY
        pygame.draw.circle(s, (56, 30, 44), pt(self.marker), int(RELAY_RADIUS), 1)
        r = 16 + 6 * pulse
        draw_dashed_circle(s, self.marker, r, ring_color, 3, dashes=18, skip=0.3)
        pygame.draw.circle(s, ring_color, pt(self.marker), 3)
        blit_text(s, self.font_small, "RELAY", (self.marker.x, self.marker.y + r + 10),
                  ring_color, "midtop")
        if self.relay_active:
            draw_dashed_circle(s, self.marker, RELAY_RADIUS - 6, COLOR_RELAY, 2,
                               dashes=30, skip=0.25)

    def _draw_aim(self, s):
        muzzle = A_POS + self.aim_dir * 34
        hit, reflected = first_wall_hit(muzzle, self.aim_dir)
        draw_dashed_line(s, muzzle, hit, COLOR_A)
        draw_dashed_line(s, hit, hit + reflected * 240, (52, 92, 116))
        pygame.draw.circle(s, COLOR_A, pt(hit), 3)
        blit_text(s, self.font_small, "A - aim with the mouse, SPACE or click to fire",
                  (24, HEIGHT - 74), COLOR_A)

    def _draw_ball(self, s):
        b = self.ball
        n = len(b.trail)
        for i, p in enumerate(b.trail):
            pygame.draw.circle(s, lerp_color(COLOR_BG, COLOR_TRAIL, (i + 1) / n), pt(p), 2)
        pygame.draw.circle(s, COLOR_BALL, pt(b.pos), int(BALL_RADIUS))
        if self.relay_active:
            draw_dashed_circle(s, b.pos, 22, COLOR_B, 2, dashes=16, skip=0.3)

    def _draw_cannons(self, s):
        pygame.draw.line(s, COLOR_A, pt(A_POS), pt(A_POS + self.aim_dir * 34), 6)
        pygame.draw.circle(s, COLOR_A, pt(A_POS), 21)
        blit_text(s, self.font_small, "A", A_POS, COLOR_BG, "center")
        near = self.ball is not None and self.ball.pos.distance_to(B_POS) < 280
        draw_dashed_circle(s, B_POS, CATCH_RADIUS, COLOR_B if near else (122, 88, 44),
                           2, dashes=32, skip=0.3)
        pygame.draw.circle(s, COLOR_B, pt(B_POS), 21)
        blit_text(s, self.font_small, "B", B_POS, COLOR_BG, "center")

    def _draw_hud(self, s):
        blit_text(s, self.font_small, f"ROUND {self.round}    SCORE {self.score}",
                  (24, 22), COLOR_TEXT)
        blit_text(s, self.font_small, "B: LEFT/RIGHT or A/D = nudge   CLICK = bumper",
                  (WIDTH - 24, 22), COLOR_B, "topright")
        blit_text(s, self.font_small,
                  "one projectile, two players - talk it through   ESC quits",
                  (WIDTH / 2, HEIGHT - 40), COLOR_DIM, "midbottom")

    def _draw_handoff(self, s):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((244, 166, 60, 24))
        s.blit(overlay, (0, 0))
        panel = pygame.Rect(0, 0, 660, 96)
        panel.center = (WIDTH // 2, 78)
        pygame.draw.rect(s, (22, 18, 16), panel, border_radius=10)
        pygame.draw.rect(s, COLOR_B, panel, 2, border_radius=10)
        blit_text(s, self.font_mid, "PLAYER B - YOUR BALL", (panel.centerx, panel.top + 12),
                  COLOR_B, "midtop")
        blit_text(s, self.font_small,
                  "one action: LEFT / RIGHT nudges the angle   CLICK drops a bumper",
                  (panel.centerx, panel.top + 46), COLOR_TEXT, "midtop")
        frac = max(0.0, self.relay_timer / RELAY_WINDOW)
        bar = pygame.Rect(0, 0, int(360 * frac), 6)
        bar.midleft = (panel.centerx - 180, panel.bottom - 14)
        pygame.draw.rect(s, COLOR_B if frac > 0.3 else COLOR_RELAY, bar, border_radius=3)

    def _draw_result(self, s):
        won, detail = self.result
        title = "RELAY COMPLETE" if won else "MISSED"
        color = COLOR_OK if won else COLOR_RELAY
        blit_text(s, self.font_big, title, (WIDTH / 2, HEIGHT / 2 - 40), color, "center")
        blit_text(s, self.font_mid, detail, (WIDTH / 2, HEIGHT / 2 + 16), COLOR_TEXT, "center")
        blit_text(s, self.font_small, "SPACE or click - next round",
                  (WIDTH / 2, HEIGHT / 2 + 58), COLOR_DIM, "center")


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("haven - relay shot")
    clock = pygame.time.Clock()
    game = RelayShot(screen)
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
        game.update(dt)
        game.draw(pygame.time.get_ticks() / 1000.0)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
