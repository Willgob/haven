"""One 60 second match."""

import math
import random

import pygame

from settings import (
    HUD_H, MATCH_TIME, HURRY_AT, MSGS, MSG_TIMES, PLAY_TOP, PLAY_BOTTOM,
    P1_X, P2_X, P1_COLORS, P2_COLORS, TARGET_ZONE, VW,
    RUBBER_DARK, RUBBER_MID, RUBBER_LIGHT,
    TARGET_DARK, TARGET_LIGHT,
    UI_DARK, UI_MID, UI_LINE, WHITE, GRAY, GOLD, RED,
    target_size, target_speed, tier_for_size,
)
from pixel_font import draw_text, text_width
from entities import (
    Bullet, Particle, Player, Ripple, ScorePop, Target, point_seg_dist,
)


class Match:
    def __init__(self, assets, sfx, mode="versus"):
        self.assets = assets
        self.sfx = sfx
        self.mode = mode  # "solo" or "versus"
        self.zone = pygame.Rect(TARGET_ZONE)
        mid_y = (PLAY_TOP + PLAY_BOTTOM) / 2
        self.p1 = Player("p1", P1_X, mid_y, assets)
        self.p2 = Player("p2", P2_X, mid_y, assets, is_cpu=(mode == "solo"))
        self.target = Target(self.zone, target_size, target_speed, sfx, assets["targets"])
        self.bullets = []
        self.particles = []
        self.pops = []
        self.ripples = []
        self.timer = MATCH_TIME
        self.elapsed = 0.0
        self.msg_idx = 0
        self.hurry = False
        self.ticks = set()
        self.banner_text = ""
        self.banner_color = WHITE
        self.banner_t = 0.0
        self.shake = 0.0
        self.over = False
        self.sudden_death = False  # tie at 0:00 -> first score wins
        self.sd_won = False
        self.winner = 0  # 1 = player 1, 2 = player 2, 0 = draw

    # helpers
    def spawn_bullet(self, player):
        mx, my = player.muzzle()
        self.bullets.append(Bullet(player.pid, mx, my, player.face))
        self.sfx.play("shoot")

    def show_banner(self, text, color, duration=2.4):
        self.banner_text = text
        self.banner_color = color
        self.banner_t = duration

    def explosion(self, x, y, colors):
        for _ in range(14):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(22.0, 78.0)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.3, 0.75),
                (random.choice(colors), UI_LINE), random.choice((1, 1, 2))))

    def wall_puff(self, x, y, color):
        for _ in range(5):
            self.particles.append(Particle(
                x, y, random.uniform(-34, 34), random.uniform(-34, 34),
                random.uniform(0.15, 0.35), (color, UI_MID), 1))

    # update
    def update(self, dt, held):
        if self.over:
            return
        self.elapsed += dt
        self.timer = max(0.0, self.timer - dt)

        while self.msg_idx < len(MSG_TIMES) and self.elapsed >= MSG_TIMES[self.msg_idx]:
            self.show_banner(MSGS[self.msg_idx], GOLD)
            self.msg_idx += 1
        if not self.hurry and self.timer <= HURRY_AT:
            self.hurry = True
            self.show_banner("HURRY!", RED, 2.0)
        whole = int(math.ceil(self.timer))
        if 1 <= whole <= 5 and whole not in self.ticks and self.timer > 0.0:
            self.ticks.add(whole)
            self.sfx.play("tick")

        self.p1.update(dt, held, self)
        if self.mode == "solo":
            self.p2.update_cpu(dt, self)
        else:
            self.p2.update(dt, held, self)

        for bullet in self.bullets:
            event = bullet.update(dt)
            if event == "wall":
                colors = P1_COLORS if bullet.owner == "p1" else P2_COLORS
                self.wall_puff(bullet.x, bullet.y, colors["light"])
                self.ripples.append(
                    Ripple(bullet.x, bullet.y, (colors["light"], colors["shade"])))
                self.sfx.play("boing")
            elif event == "fizzle":
                self.wall_puff(bullet.x, bullet.y, GRAY)
        self._collisions()
        self.bullets = [b for b in self.bullets if b.alive]

        self.target.update(dt, self.elapsed)
        self.particles = [p for p in self.particles if p.update(dt)]
        self.pops = [p for p in self.pops if p.update(dt)]
        self.ripples = [r for r in self.ripples if r.update(dt)]
        self.banner_t = max(0.0, self.banner_t - dt)
        self.shake = max(0.0, self.shake - dt * 9.0)

        if self.timer <= 0.0001 and not self.sudden_death:
            if self.p1.score == self.p2.score:
                # tied, so keep playing until someone scores
                self.sudden_death = True
                self.show_banner("SUDDEN DEATH - FIRST SCORE WINS!", RED, 3.0)
                self.sfx.play("start")
            else:
                self._finish()

    def _collisions(self):
        target = self.target
        reach = target.radius() + 1.5
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            if point_seg_dist(target.x, target.y, bullet.px, bullet.py,
                              bullet.x, bullet.y) <= reach:
                base_points, _label, _color = target.hit(bullet.x)
                # bank shots pay: each wall bounce multiplies the tier
                points = base_points * (1 + bullet.bounces)
                scorer = self.p1 if bullet.owner == "p1" else self.p2
                scorer.score += points
                self.pops.append(ScorePop(bullet.x, bullet.y - 6, f"+{points}",
                                          scorer.colors["light"]))
                if bullet.bounces == 1:
                    self.pops.append(ScorePop(bullet.x, bullet.y - 13,
                                              "BANK SHOT!", GOLD))
                elif bullet.bounces >= 2:
                    self.pops.append(ScorePop(bullet.x, bullet.y - 13,
                                              "DOUBLE BANK!", GOLD))
                self.explosion(bullet.x, bullet.y,
                               (WHITE, scorer.colors["body"], scorer.colors["light"]))
                self.ripples.append(Ripple(bullet.x, bullet.y,
                                           (TARGET_LIGHT, TARGET_DARK), 0.34))
                self.shake = 2.2
                self.sfx.play("hit")
                self.sfx.play("boing_low")
                bullet.alive = False
                if self.sudden_death:
                    self._finish()
                    break

    def _finish(self):
        self.over = True
        self.sd_won = self.sudden_death
        self.banner_t = 0.0
        if self.p1.score > self.p2.score:
            self.winner = 1
        elif self.p2.score > self.p1.score:
            self.winner = 2
        else:
            self.winner = 0
        self.sfx.play("win")

    # draw
    def draw(self, surf, t):
        sdx = sdy = 0
        if self.shake > 0.0:
            sdx = int(round(random.uniform(-1, 1) * self.shake))
            sdy = int(round(random.uniform(-1, 1) * self.shake))
        surf.blit(self.assets["background"], (0, 0))
        for i, (x, y, _c) in enumerate(self.assets["stars"]):
            if (int(t * 3.0) + i) % 9 == 0:
                surf.fill((196, 206, 240), (x, y, 1, 1))
        self._draw_zone(surf, sdx)
        self.target.draw(surf, t, sdx, sdy)
        for bullet in self.bullets:
            bullet.draw(surf, self.assets["bullets"][bullet.owner], sdx, sdy)
        self.p1.draw(surf, t, sdx, sdy)
        self.p2.draw(surf, t, sdx, sdy)
        for particle in self.particles:
            particle.draw(surf, sdx, sdy)
        for pop in self.pops:
            pop.draw(surf, sdx, sdy)
        self._draw_walls(surf)
        for ripple in self.ripples:
            ripple.draw(surf, sdx, sdy)
        self._draw_banner(surf)
        self._draw_hud(surf, t)
        surf.blit(self.assets["scanlines"], (0, 0))

    def _draw_zone(self, surf, dx):
        zone = self.zone
        for y in range(zone.top, zone.bottom, 4):
            surf.fill((52, 60, 104), (zone.left + dx, y, 1, 2))
            surf.fill((52, 60, 104), (zone.right - 1 + dx, y, 1, 2))

    def _draw_walls(self, surf):
        # rubber walls, stitching and corner pads
        pygame.draw.rect(surf, RUBBER_MID, (0, HUD_H, VW, 2))
        pygame.draw.rect(surf, RUBBER_DARK, (0, HUD_H + 2, VW, 1))
        pygame.draw.rect(surf, RUBBER_MID, (0, PLAY_BOTTOM + 1, VW, 2))
        pygame.draw.rect(surf, RUBBER_MID, (0, HUD_H, 2, 153))
        pygame.draw.rect(surf, RUBBER_MID, (VW - 2, HUD_H, 2, 153))
        for y in range(HUD_H + 3, PLAY_BOTTOM + 1, 5):     # stitching
            surf.fill(RUBBER_LIGHT, (1, y, 1, 1))
            surf.fill(RUBBER_LIGHT, (VW - 2, y, 1, 1))
        for x in range(4, VW - 4, 5):
            surf.fill(RUBBER_LIGHT, (x, HUD_H + 1, 1, 1))
            surf.fill(RUBBER_LIGHT, (x, PLAY_BOTTOM + 1, 1, 1))
        self._bumper_pad(surf, 2, HUD_H + 2)
        self._bumper_pad(surf, VW - 6, HUD_H + 2)
        self._bumper_pad(surf, 2, PLAY_BOTTOM - 2)
        self._bumper_pad(surf, VW - 6, PLAY_BOTTOM - 2)

    def _bumper_pad(self, surf, x, y):
        pygame.draw.rect(surf, RUBBER_DARK, (x, y, 4, 4))
        pygame.draw.rect(surf, RUBBER_LIGHT, (x, y, 4, 4), 1)
        pygame.draw.rect(surf, GOLD, (x + 1, y + 1, 2, 2))

    def _draw_banner(self, surf):
        if self.banner_t <= 0.0:
            return
        if self.banner_t < 0.5 and int(self.banner_t * 14) % 2 == 0:
            return
        width = text_width(self.banner_text, 1) + 8
        x = VW // 2 - width // 2
        pygame.draw.rect(surf, UI_DARK, (x, 30, width, 11))
        pygame.draw.rect(surf, UI_LINE, (x, 30, width, 11), 1)
        draw_text(surf, self.banner_text, (VW // 2, 32), self.banner_color, 1, "center")

    def _draw_hud(self, surf, t):
        pygame.draw.rect(surf, UI_DARK, (0, 0, VW, HUD_H))
        pygame.draw.rect(surf, UI_MID, (0, HUD_H - 1, VW, 1))
        draw_text(surf, "P1", (6, 4), P1_COLORS["body"], 1)
        draw_text(surf, f"{self.p1.score:02d}", (6, 11), P1_COLORS["light"], 2)
        p2_label = "CPU" if self.mode == "solo" else "P2"
        draw_text(surf, p2_label, (VW - 6, 4), P2_COLORS["shade"], 1, "right")
        draw_text(surf, f"{self.p2.score:02d}", (VW - 6, 11), P2_COLORS["light"], 2, "right")
        if self.p1.score > self.p2.score:          # who has the most points
            draw_text(surf, ">", (24, 13), P1_COLORS["light"], 1)
        elif self.p2.score > self.p1.score:
            draw_text(surf, "<", (VW - 24, 13), P2_COLORS["light"], 1, "right")
        if self.sudden_death:
            if int(t * 4) % 2 == 0:
                draw_text(surf, "SD", (VW // 2, 3), RED, 2, "center")
            draw_text(surf, "FIRST SCORE WINS", (VW // 2, 16), GOLD, 1, "center")
        else:
            seconds = int(math.ceil(self.timer))
            minutes, secs = divmod(seconds, 60)
            color = RED if (self.timer <= HURRY_AT and int(t * 4) % 2 == 0) else WHITE
            draw_text(surf, f"{minutes}:{secs:02d}", (VW // 2, 3), color, 2, "center")
            points, name, tier_color = tier_for_size(target_size(self.elapsed))
            draw_text(surf, f"TARGET {name} +{points}", (VW // 2, 16), tier_color, 1, "center")
