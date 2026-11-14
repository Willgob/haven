"""BOUNCE BACK - Pixel Arcade.

A two-player retro arcade shooter on one shared arena. Both gunners fire at a
bouncing energy core that shrinks and speeds up as the 60-second match runs;
smaller targets score more points. Rendered on a 320x180 virtual screen
scaled x4 with nearest-neighbour for a genuine 16-bit look.

Run with:  python main.py
"""

import random

import pygame

from settings import (
    FPS, GOLD, GREEN, GRAY, KEY_ACTIONS, RESULT_MSGS,
    SCALE, VH, VW, WIN_H, WIN_W,
)
from pixel_art import build_assets
from sfx import Sfx
from entities import Target
from match import Match
from screens import Button, draw_menu, draw_pause, draw_results


class Game:
    """State machine + main loop. States: menu, playing, paused, results."""

    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("BOUNCE BACK - Pixel Arcade")
        self.virtual = pygame.Surface((VW, VH))
        self.assets = build_assets()
        self.sfx = Sfx()
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.match = None
        self.held = set()
        self.t = 0.0
        self.running = True
        self.result_msg = ""
        self.confetti = []
        self.menu_target = Target(pygame.Rect(8, 4, 304, 18),
                                  lambda e: 10.0, lambda e: 26.0,
                                  self.sfx, self.assets["targets"])
        self.buttons = self._build_buttons()

    # ---------------------------------------------------------------- setup
    def _build_buttons(self):
        menu = [Button(160, 128, 104, 20, "PLAY", GOLD, 2, "play")]
        pause = [
            Button(160, 82, 116, 16, "RESUME", GREEN, 2, "resume"),
            Button(160, 102, 116, 16, "RESTART", GOLD, 2, "restart"),
            Button(160, 122, 116, 16, "MAIN MENU", GRAY, 2, "menu"),
        ]
        results = [
            Button(160, 114, 124, 16, "PLAY AGAIN", GOLD, 2, "restart"),
            Button(160, 136, 124, 16, "MAIN MENU", GRAY, 2, "menu"),
        ]
        return {"menu": menu, "pause": pause, "results": results}

    # ------------------------------------------------------------- transitions
    def start_match(self):
        self.match = Match(self.assets, self.sfx)
        self.state = "playing"
        self.sfx.play("start")

    def _button_action(self, action):
        if action == "play" or action == "restart":
            self.start_match()
        elif action == "resume":
            self.state = "playing"
        elif action == "menu":
            self.state = "menu"

    def _enter_results(self):
        self.state = "results"
        self.result_msg = random.choice(RESULT_MSGS)
        palette = (
            self.assets["players"]["p1"]["colors"]["light"],
            self.assets["players"]["p2"]["colors"]["light"],
            (240, 244, 255), (255, 202, 84),
        )
        self.confetti = [
            {"x": random.uniform(0, VW), "y": random.uniform(-50, -2),
             "vy": random.uniform(18, 46), "vx": random.uniform(-7, 7),
             "c": random.choice(palette)}
            for _ in range(46)
        ]

    # ------------------------------------------------------------------ events
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            action = KEY_ACTIONS.get(event.key)
            if action:
                if event.type == pygame.KEYDOWN:
                    self.held.add(action)
                else:
                    self.held.discard(action)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos[0] // SCALE, event.pos[1] // SCALE
            for button in self.buttons.get(self.state, ()):
                if button.rect.collidepoint((mx, my)):
                    self.sfx.play("select")
                    self._button_action(button.action)
                    return

        if event.type == pygame.KEYDOWN:
            self._keydown(event.key)

        focus_lost = getattr(pygame, "WINDOWFOCUSLOST", None)
        if focus_lost is not None and event.type == focus_lost:
            self.held.clear()
            if self.state == "playing":
                self.state = "paused"

    def _keydown(self, key):
        if self.state == "menu":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_match()
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == "playing":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
                self.sfx.play("select")
        elif self.state == "paused":
            if key == pygame.K_ESCAPE:
                self.state = "playing"
            elif key == pygame.K_r:
                self.start_match()
            elif key == pygame.K_m:
                self.state = "menu"
        elif self.state == "results":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_match()
            elif key in (pygame.K_ESCAPE, pygame.K_m):
                self.state = "menu"

    # ------------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        if self.state == "menu":
            self.menu_target.update(dt, 0.0)
        elif self.state == "playing":
            self.match.update(dt, lambda key: key in self.held)
            if self.match.over:
                self._enter_results()
        elif self.state == "results":
            for bit in self.confetti:
                bit["x"] += bit["vx"] * dt
                bit["y"] += bit["vy"] * dt
                if bit["y"] > VH:
                    bit["y"] = -2
                    bit["x"] = random.uniform(0, VW)

    # -------------------------------------------------------------------- draw
    def draw(self):
        surf = self.virtual
        mouse = (pygame.mouse.get_pos()[0] // SCALE, pygame.mouse.get_pos()[1] // SCALE)
        if self.state == "menu":
            draw_menu(surf, self.assets, self.t, self.menu_target,
                      self.buttons["menu"], mouse)
        elif self.state == "playing":
            self.match.draw(surf, self.t)
        elif self.state == "paused":
            draw_pause(surf, self.match, self.t, self.buttons["pause"], mouse)
        elif self.state == "results":
            draw_results(surf, self.match, self.t, self.buttons["results"],
                         mouse, self.confetti, self.result_msg)
        pygame.transform.scale(surf, (WIN_W, WIN_H), self.window)
        pygame.display.flip()

    # --------------------------------------------------------------------- run
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)   # frame-rate independent
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
