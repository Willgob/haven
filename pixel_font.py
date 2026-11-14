"""Hand-made 3x5 bitmap font. No font files needed."""

import pygame

GLYPHS = {
    "A": (".X.", "X.X", "XXX", "X.X", "X.X"),
    "B": ("XX.", "X.X", "XX.", "X.X", "XX."),
    "C": (".XX", "X..", "X..", "X..", ".XX"),
    "D": ("XX.", "X.X", "X.X", "X.X", "XX."),
    "E": ("XXX", "X..", "XX.", "X..", "XXX"),
    "F": ("XXX", "X..", "XX.", "X..", "X.."),
    "G": (".XX", "X..", "X.X", "X.X", ".XX"),
    "H": ("X.X", "X.X", "XXX", "X.X", "X.X"),
    "I": ("XXX", ".X.", ".X.", ".X.", "XXX"),
    "J": ("..X", "..X", "..X", "X.X", ".X."),
    "K": ("X.X", "X.X", "XX.", "X.X", "X.X"),
    "L": ("X..", "X..", "X..", "X..", "XXX"),
    "M": ("X.X", "XXX", "X.X", "X.X", "X.X"),
    "N": ("XX.", "X.X", "X.X", "X.X", "X.X"),
    "O": ("XXX", "X.X", "X.X", "X.X", "XXX"),
    "P": ("XXX", "X.X", "XXX", "X..", "X.."),
    "Q": ("XXX", "X.X", "X.X", ".XX", "..X"),
    "R": ("XXX", "X.X", "XX.", "X.X", "X.X"),
    "S": (".XX", "X..", ".X.", "..X", "XX."),
    "T": ("XXX", ".X.", ".X.", ".X.", ".X."),
    "U": ("X.X", "X.X", "X.X", "X.X", "XXX"),
    "V": ("X.X", "X.X", "X.X", "X.X", ".X."),
    "W": ("X.X", "X.X", "X.X", "XXX", "X.X"),
    "X": ("X.X", "X.X", ".X.", "X.X", "X.X"),
    "Y": ("X.X", "X.X", ".X.", ".X.", ".X."),
    "Z": ("XXX", "..X", ".X.", "X..", "XXX"),
    "0": ("XXX", "X.X", "X.X", "X.X", "XXX"),
    "1": (".X.", "XX.", ".X.", ".X.", "XXX"),
    "2": ("XXX", "..X", "XXX", "X..", "XXX"),
    "3": ("XXX", "..X", "XXX", "..X", "XXX"),
    "4": ("X.X", "X.X", "XXX", "..X", "..X"),
    "5": ("XXX", "X..", "XXX", "..X", "XXX"),
    "6": ("XXX", "X..", "XXX", "X.X", "XXX"),
    "7": ("XXX", "..X", "..X", "..X", "..X"),
    "8": ("XXX", "X.X", "XXX", "X.X", "XXX"),
    "9": ("XXX", "X.X", "XXX", "..X", "XXX"),
    "!": (".X.", ".X.", ".X.", "...", ".X."),
    "?": ("XX.", "..X", ".X.", "...", ".X."),
    ":": ("...", ".X.", "...", ".X.", "..."),
    ".": ("...", "...", "...", "...", ".X."),
    ",": ("...", "...", "...", ".X.", "X.."),
    "'": (".X.", ".X.", "...", "...", "..."),
    "-": ("...", "...", "XXX", "...", "..."),
    "+": ("...", ".X.", "XXX", ".X.", "..."),
    "=": ("...", "XXX", "...", "XXX", "..."),
    "/": ("..X", "..X", ".X.", "X..", "X.."),
    "(": ("..X", ".X.", ".X.", ".X.", "..X"),
    ")": ("X..", ".X.", ".X.", ".X.", "X.."),
    "%": ("X.X", "..X", ".X.", "X..", "X.X"),
    ">": ("X..", ".X.", "..X", ".X.", "X.."),
    "<": ("..X", ".X.", "X..", ".X.", "..X"),
    " ": ("...", "...", "...", "...", "..."),
}

_cache = {}
_warned = set()


def text_width(text, scale=1):
    return (len(text) * 4 - 1) * scale


def text_surface(text, color, scale=1):
    text = text.upper()
    key = (text, color, scale)
    surf = _cache.get(key)
    if surf is not None:
        return surf
    surf = pygame.Surface((max(text_width(text, scale), 1), 5 * scale), pygame.SRCALPHA)
    x = 0
    for ch in text:
        glyph = GLYPHS.get(ch)
        if glyph is None:
            glyph = GLYPHS["?"]
            if ch not in _warned:
                _warned.add(ch)
                print(f"[pixel_font] missing glyph {ch!r} - rendering '?'")
        for row in range(5):
            line = glyph[row]
            for col in range(3):
                if line[col] == "X":
                    surf.fill(color, (x + col * scale, row * scale, scale, scale))
        x += 4 * scale
    _cache[key] = surf
    if len(_cache) > 900:          # don't let the cache grow forever
        _cache.clear()
    return surf


def draw_text(surf, text, pos, color, scale=1, align="left"):
    ts = text_surface(text, color, scale)
    x, y = pos
    if align == "center":
        x -= ts.get_width() / 2
    elif align == "right":
        x -= ts.get_width()
    surf.blit(ts, (round(x), round(y)))
