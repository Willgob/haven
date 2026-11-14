"""Global tuning, palette and arena geometry for BOUNCE BACK - Pixel Arcade.

Everything is rendered on a low-resolution virtual screen (320x180) which is
scaled up x4 with nearest-neighbour blitting, so the whole game stays
genuinely pixelated instead of merely using pixel-style text.
"""

import pygame

# --- screen -----------------------------------------------------------------
VW, VH = 320, 180            # virtual low-res screen
SCALE = 4                    # window scale factor (nearest-neighbour)
WIN_W, WIN_H = VW * SCALE, VH * SCALE
FPS = 60

# --- match --------------------------------------------------------------------
MATCH_TIME = 60.0            # seconds per competitive match
HURRY_AT = 10.0              # remaining time that triggers the HURRY banner

# --- arena geometry (virtual pixels) ------------------------------------------
HUD_H = 23                   # scoreboard strip height
TOP_WALL_Y = HUD_H           # 2px wall right below the HUD
PLAY_TOP = HUD_H + 3         # first playable row (wall + shadow line)
PLAY_BOTTOM = 173            # last playable row
BOTTOM_WALL_Y = 174          # 2px wall at floor level
ARENA_L = 2                  # interior left edge (side walls are 2px)
ARENA_R = 317                # interior right edge

P1_X = 26                    # player 1 column (left side)
P2_X = 294                   # player 2 column (right side)

# central zone the target bounces around (left, top, width, height)
TARGET_ZONE = (96, 34, 128, 130)

# --- players --------------------------------------------------------------------
PLAYER_SPEED = 85.0          # px/s
GUN_LEN = 8                  # gun barrel length in pixels
MUZZLE_DIST = 13             # muzzle distance from the player center
BULLET_Y_OFFSET = 2          # bullet row relative to player center

SHOT_COOLDOWN = 0.33
BULLET_SPEED = 150.0
BULLET_LIFETIME = 3.2        # bullets ricochet for a while, then fizzle out
BULLET_MAX_BOUNCES = 2       # missed shots bounce back - keep trying!
BULLET_CAP = 24              # safety cap on simultaneous projectiles

# --- target ----------------------------------------------------------------------
TARGET_SIZE_START = 16.0     # diameter in virtual pixels
TARGET_SIZE_END = 6.0
TARGET_SPEED_START = 40.0
TARGET_SPEED_END = 110.0

# size thresholds -> points, label, colour (largest first)
TIER_TABLE = (
    (13.5, 1, "LARGE", (240, 244, 255)),
    (10.0, 3, "MEDIUM", (255, 202, 84)),
    (7.0, 5, "SMALL", (255, 150, 90)),
    (0.0, 10, "TINY", (244, 84, 96)),
)

POP_LIFE = 0.9               # floating score popup lifetime

# --- encouragement -----------------------------------------------------------------
MSG_TIMES = (15.0, 30.0, 45.0)
MSGS = ("KEEP FIRING!", "STAY SHARP!", "BOUNCE BACK!")
RESULT_MSGS = (
    "GREAT MATCH - EVERY SHOT COUNTS!",
    "NOTHING BEATS A REMATCH!",
    "PERSISTENCE WINS MATCHES!",
    "BOUNCE BACK AND GO AGAIN!",
)

# --- palette -----------------------------------------------------------------------
NAVY = (13, 15, 34)
UI_DARK = (18, 21, 44)
UI_MID = (30, 35, 68)
UI_LINE = (58, 66, 118)
WHITE = (240, 244, 255)
GRAY = (110, 118, 152)
GOLD = (255, 202, 84)
RED = (244, 84, 96)
GREEN = (124, 220, 144)

P1_COLORS = {
    "outline": (16, 26, 58), "body": (64, 140, 246), "light": (158, 208, 255),
    "shade": (38, 82, 168), "visor": (10, 16, 38), "eye": (235, 245, 255),
    "metal": (96, 108, 150),
}
P2_COLORS = {
    "outline": (66, 30, 10), "body": (247, 146, 50), "light": (255, 214, 132),
    "shade": (188, 94, 24), "visor": (36, 18, 8), "eye": (255, 246, 232),
    "metal": (158, 122, 88),
}

TARGET_BODY = (236, 76, 118)
TARGET_LIGHT = (255, 176, 208)
TARGET_DARK = (98, 26, 54)
TARGET_CORE = (255, 242, 250)

# --- input ---------------------------------------------------------------------------
CONTROLS = {
    "p1": ("p1_up", "p1_down", "p1_shoot"),
    "p2": ("p2_up", "p2_down", "p2_shoot"),
}
KEY_ACTIONS = {
    pygame.K_w: "p1_up", pygame.K_s: "p1_down", pygame.K_SPACE: "p1_shoot",
    pygame.K_UP: "p2_up", pygame.K_DOWN: "p2_down",
    pygame.K_RETURN: "p2_shoot", pygame.K_KP_ENTER: "p2_shoot",
}


def tier_for_size(size):
    """Map a target diameter to (points, label, colour)."""
    for threshold, pts, name, color in TIER_TABLE:
        if size >= threshold:
            return pts, name, color
    return TIER_TABLE[-1][1], TIER_TABLE[-1][2], TIER_TABLE[-1][3]


def target_size(elapsed):
    """Target diameter shrinks steadily over the match (progressive, not random)."""
    t = min(1.0, max(0.0, elapsed / MATCH_TIME))
    return TARGET_SIZE_START + (TARGET_SIZE_END - TARGET_SIZE_START) * t


def target_speed(elapsed):
    """Target speed ramps up steadily over the match."""
    t = min(1.0, max(0.0, elapsed / MATCH_TIME))
    return TARGET_SPEED_START + (TARGET_SPEED_END - TARGET_SPEED_START) * t
