"""UI screens: pixel buttons, main menu, pause overlay and results screen."""

import math

import pygame

from settings import (
    VH, VW, UI_DARK, UI_MID, UI_LINE, WHITE, GRAY, GOLD, GREEN,
    P1_COLORS, P2_COLORS,
)
from pixel_font import draw_text, text_width


class Button:
    """A chunky pixel button with hover highlight; clickable with the mouse."""

    def __init__(self, cx, cy, w, h, label, accent, scale=2, action=None):
        self.rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
        self.label = label
        self.accent = accent
        self.scale = scale
        self.action = action

    def draw(self, surf, mouse):
        hovered = self.rect.collidepoint(mouse)
        pygame.draw.rect(surf, (8, 10, 22), self.rect.move(2, 2))
        pygame.draw.rect(surf, (38, 46, 88) if hovered else (24, 28, 56), self.rect)
        pygame.draw.rect(surf, self.accent if hovered else UI_LINE, self.rect, 2)
        color = self.accent if hovered else WHITE
        y = self.rect.centery - (5 * self.scale) // 2
        draw_text(surf, self.label, (self.rect.centerx, y), color, self.scale, "center")


# --------------------------------------------------------------------- menu
def draw_menu(surf, assets, t, demo_target, buttons, mouse):
    surf.blit(assets["background"], (0, 0))
    for i, (x, y, _c) in enumerate(assets["stars"]):
        if (int(t * 3.0) + i) % 9 == 0:
            surf.fill((196, 206, 240), (x, y, 1, 1))
    demo_target.draw(surf, t, 0, 0)
    for pid, x in (("p1", 26), ("p2", 294)):
        player = assets["players"][pid]
        frames = player["frames"] if int(t * 3.0) % 2 == 0 else player["frames_off"]
        surf.blit(frames[0], (x - 5, 164))

    ty = 30 - (1 if int(t * 2.0) % 2 else 0)      # chunky 1px title bounce
    x0 = VW // 2 - text_width("BOUNCE BACK", 4) // 2
    w1 = text_width("BOUNCE ", 4)
    draw_text(surf, "BOUNCE BACK", (x0 + 2, ty + 2), (6, 7, 16), 4)
    draw_text(surf, "BOUNCE", (x0, ty), P1_COLORS["light"], 4)
    draw_text(surf, "BACK", (x0 + w1, ty), P2_COLORS["light"], 4)
    draw_text(surf, "PIXEL ARCADE - SOLO OR TWO PLAYER SHOWDOWN", (VW // 2, 51), GRAY, 1, "center")

    panel = pygame.Rect(30, 58, 260, 52)
    pygame.draw.rect(surf, UI_DARK, panel)
    pygame.draw.rect(surf, UI_LINE, panel, 1)
    draw_text(surf, "PLAYER 1", (44, 63), P1_COLORS["light"], 1)
    draw_text(surf, "W/S - MOVE", (44, 73), WHITE, 1)
    draw_text(surf, "SPACE - SHOOT", (44, 83), WHITE, 1)
    draw_text(surf, "PLAYER 2", (170, 63), P2_COLORS["light"], 1)
    draw_text(surf, "UP/DOWN - MOVE", (170, 73), WHITE, 1)
    draw_text(surf, "ENTER - SHOOT", (170, 83), WHITE, 1)
    draw_text(surf, "SMALLER TARGET = MORE POINTS", (VW // 2, 97), GOLD, 1, "center")

    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "CLICK OR PRESS 1 / 2", (VW // 2, 158), GRAY, 1, "center")
    draw_text(surf, "ESC QUITS", (VW // 2, 168), GRAY, 1, "center")


# --------------------------------------------------------------------- pause
def draw_pause(surf, match, t, buttons, mouse):
    match.draw(surf, t)
    dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
    dim.fill((8, 9, 18, 178))
    surf.blit(dim, (0, 0))
    panel = pygame.Rect(84, 46, 152, 92)
    pygame.draw.rect(surf, (10, 12, 26), panel.move(2, 2))
    pygame.draw.rect(surf, UI_DARK, panel)
    pygame.draw.rect(surf, UI_LINE, panel, 2)
    draw_text(surf, "PAUSED", (VW // 2, 54), WHITE, 3, "center")
    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "ESC RESUME - R RESTART - M MENU", (VW // 2, 144), GRAY, 1, "center")


# ------------------------------------------------------------------- results
def draw_results(surf, match, t, buttons, mouse, confetti, message):
    match.draw(surf, t)
    dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
    dim.fill((8, 9, 18, 172))
    surf.blit(dim, (0, 0))
    for bit in confetti:
        pygame.draw.rect(surf, bit["c"], (int(bit["x"]), int(bit["y"]), 1, 1))

    if match.mode == "solo":
        if match.winner == 1:
            title, color = "YOU WIN!", P1_COLORS["light"]
        elif match.winner == 2:
            title, color = "CPU WINS!", P2_COLORS["light"]
        else:
            title, color = "DRAW MATCH!", GOLD
        left_label, right_label = "YOU", "CPU"
    else:
        if match.winner == 1:
            title, color = "PLAYER 1 WINS!", P1_COLORS["light"]
        elif match.winner == 2:
            title, color = "PLAYER 2 WINS!", P2_COLORS["light"]
        else:
            title, color = "DRAW MATCH!", GOLD
        left_label, right_label = "P1", "P2"
    draw_text(surf, title, (VW // 2 + 2, 42), (6, 7, 16), 3, "center")
    draw_text(surf, title, (VW // 2, 40), color, 3, "center")

    draw_text(surf, f"{left_label} {match.p1.score:02d}", (150, 68), P1_COLORS["light"], 2, "right")
    draw_text(surf, "-", (160, 68), WHITE, 2, "center")
    draw_text(surf, f"{match.p2.score:02d} {right_label}", (170, 68), P2_COLORS["light"], 2, "left")

    draw_text(surf, message, (VW // 2, 92), GOLD, 1, "center")
    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "ENTER PLAY AGAIN - M MENU", (VW // 2, 154), GRAY, 1, "center")
