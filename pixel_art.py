"""Procedural pixel-art assets for BOUNCE BACK.

Every sprite is baked once at startup from small character maps / drawing
routines: no image files needed, no per-frame surface creation.
"""

import math
import random

import pygame

from settings import (
    VH, VW, NAVY, P1_COLORS, P2_COLORS,
    TARGET_BODY, TARGET_LIGHT, TARGET_DARK, TARGET_CORE,
)


def _sheet(rows, palette):
    """Bake a character map (tuple of strings) into a transparent surface."""
    width = len(rows[0])
    surf = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return surf


# --------------------------------------------------------------------------
# Player gunners - chunky 10x13 sprites with helmet, visor and blinking antenna
# --------------------------------------------------------------------------
_PLAYER_TOP = (
    "....ol....",
    "...oooo...",
    "..obbbbo..",
    "..obddeo..",
    "..obbbbo..",
    "...oooo...",
    "..obbbbo..",
    ".obbbbbbo.",
    ".obsbbsbo.",
    "..obbbbo..",
)
_LEGS_A = ("..ob..bo..", "..ob..bo..", "..oo..oo..")   # legs together
_LEGS_B = (".ob....bo.", ".ob....bo.", ".oo....oo.")   # legs apart (stride)

_FLASH_SMALL = (".X.", "XXX", ".X.")
_FLASH_BIG = (".lWl.", "lWWWl", ".lWl.")

_BULLET_F1 = ("dbbll", "dbbbb")
_BULLET_F2 = ("lbllb", "dbbbb")


def _player_palette(scheme, light_on):
    pal = {
        "o": scheme["outline"], "b": scheme["body"], "s": scheme["shade"],
        "d": scheme["visor"], "e": scheme["eye"],
        "l": scheme["light"] if light_on else scheme["outline"],
    }
    return pal


def _build_players():
    players = {}
    for pid, scheme in (("p1", P1_COLORS), ("p2", P2_COLORS)):
        pal_on = _player_palette(scheme, True)
        pal_off = _player_palette(scheme, False)
        frames = [_sheet(_PLAYER_TOP + legs, pal_on) for legs in (_LEGS_A, _LEGS_B)]
        frames_off = [_sheet(_PLAYER_TOP + legs, pal_off) for legs in (_LEGS_A, _LEGS_B)]
        if pid == "p2":                      # player 2 faces left
            frames = [pygame.transform.flip(f, True, False) for f in frames]
            frames_off = [pygame.transform.flip(f, True, False) for f in frames_off]
        flash_small = _sheet(_FLASH_SMALL, {"X": (255, 255, 228)})
        flash_big = _sheet(_FLASH_BIG, {"W": (255, 255, 235), "l": scheme["light"]})
        players[pid] = {
            "frames": frames, "frames_off": frames_off, "colors": scheme,
            "flash_small": flash_small, "flash_big": flash_big,
        }
    return players


def _build_bullets():
    bullets = {}
    for pid, scheme in (("p1", P1_COLORS), ("p2", P2_COLORS)):
        pal = {"d": scheme["shade"], "b": scheme["body"], "l": scheme["light"]}
        f1 = _sheet(_BULLET_F1, pal)
        f2 = _sheet(_BULLET_F2, pal)
        if pid == "p2":
            f1 = pygame.transform.flip(f1, True, False)
            f2 = pygame.transform.flip(f2, True, False)
        bullets[pid] = (f1, f2)
    return bullets


# --------------------------------------------------------------------------
# Target - an animated pixel "energy core" octagon in many sizes
# --------------------------------------------------------------------------
def _build_targets():
    targets = {}
    for diameter in range(4, 19):
        frames, whites = [], []
        radius = diameter / 2.0
        pad = 2
        size = diameter + pad * 2
        center = (size - 1) / 2.0
        for frame_idx in range(4):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            white = pygame.Surface((size, size), pygame.SRCALPHA)
            for py in range(size):
                for px in range(size):
                    dx, dy = px - center, py - center
                    box = max(abs(dx), abs(dy))
                    manhattan = abs(dx) + abs(dy)
                    if box <= radius + 0.26 and manhattan <= radius * 1.5 + 0.5:
                        edge = box >= radius - 0.55 or manhattan >= radius * 1.5 - 0.55
                        core = box <= max(1.1, radius * 0.34)
                        if edge:
                            color = TARGET_DARK
                        elif core:
                            color = TARGET_CORE
                        else:
                            color = TARGET_BODY
                        surf.set_at((px, py), color)
                        white.set_at((px, py), (252, 252, 255))
                # rotating highlight spark
            angle = frame_idx * (math.pi / 2) + math.pi / 4
            hx = int(round(center + math.cos(angle) * radius * 0.62))
            hy = int(round(center + math.sin(angle) * radius * 0.62))
            if 0 <= hx < size and 0 <= hy < size and surf.get_at((hx, hy))[3] > 0:
                surf.set_at((hx, hy), TARGET_LIGHT)
            frames.append(surf)
            whites.append(white)
        targets[diameter] = {"frames": frames, "white": whites}
    return targets


# --------------------------------------------------------------------------
# Background - retro night skyline with lit windows and a starfield
# --------------------------------------------------------------------------
def _build_background():
    rng = random.Random(7)
    surf = pygame.Surface((VW, VH))
    surf.fill(NAVY)
    stars = []
    for _ in range(46):
        x = rng.randrange(4, VW - 4)
        y = rng.randrange(4, 110)
        color = rng.choice(((58, 68, 108), (94, 106, 148), (148, 158, 198)))
        stars.append((x, y, color))
        surf.fill(color, (x, y, 1, 1))
    floor_y = 174
    # far skyline
    x = 0
    while x < VW:
        w = rng.randrange(8, 22)
        h = rng.randrange(8, 26)
        pygame.draw.rect(surf, (18, 20, 44), (x, floor_y - h, w, h))
        for _ in range(rng.randrange(1, 4)):
            wx = x + rng.randrange(1, max(2, w - 2))
            wy = floor_y - h + rng.randrange(2, max(3, h - 2))
            if 0 <= wx < VW and floor_y - h + 2 <= wy < floor_y - 1:
                surf.set_at((wx, wy), (70, 90, 140) if rng.random() < 0.7 else (172, 128, 76))
        x += w + rng.randrange(1, 4)
    # near skyline with antenna beacons
    x = 0
    while x < VW:
        w = rng.randrange(10, 26)
        h = rng.randrange(14, 34)
        pygame.draw.rect(surf, (24, 27, 56), (x, floor_y - h, w, h))
        if rng.random() < 0.55:
            surf.set_at((x + w // 2, floor_y - h - 1), (255, 200, 80))
        x += w + rng.randrange(2, 6)
    # floor strip
    pygame.draw.rect(surf, (30, 34, 66), (0, floor_y, VW, VH - floor_y))
    for gx in range(0, VW, 8):
        surf.fill((46, 52, 92), (gx, floor_y + 2, 2, 1))
    return surf, stars


def _build_scanlines():
    surf = pygame.Surface((VW, VH), pygame.SRCALPHA)
    for y in range(1, VH, 2):
        surf.fill((0, 0, 0, 28), (0, y, VW, 1))
    return surf


def build_assets():
    background, stars = _build_background()
    return {
        "players": _build_players(),
        "bullets": _build_bullets(),
        "targets": _build_targets(),
        "background": background,
        "stars": stars,
        "scanlines": _build_scanlines(),
    }
