"""Tiny synthesized retro sound effects - no audio files or extra libraries.

All sounds are generated once as raw 16-bit PCM arrays (square waves, noise
bursts and a little win jingle) and wrapped in pygame mixer Sounds. If the
audio device cannot be initialised (e.g. headless environments) the class
silently degrades to a no-op so the game never crashes on sound.
"""

import array
import math
import random

import pygame

RATE = 22050


def _seq(ms, fn, vol):
    n = max(1, int(RATE * ms / 1000))
    out = array.array("h", bytes(2 * n))
    for i in range(n):
        value = fn(i / n)
        out[i] = int(max(-1.0, min(1.0, value)) * 32767 * vol)
    return out


def _square(f0, f1, ms, vol=0.2):
    """Square wave sweeping from f0 to f1 with a simple decay envelope."""
    state = {"phase": 0.0}

    def fn(t):
        freq = f0 + (f1 - f0) * t
        state["phase"] += freq / RATE
        wave = 1.0 if (state["phase"] % 1.0) < 0.5 else -1.0
        return wave * (1.0 - t)

    return _seq(ms, fn, vol)


def _noise(ms, vol=0.2):
    def fn(t):
        return random.uniform(-1.0, 1.0) * (1.0 - t)

    return _seq(ms, fn, vol)


def _boing(f0, f1, ms, wobble, vol):
    """Cartoon spring: a sine sweep with vibrato that dies away quickly."""
    state = {"phase": 0.0, "wob": 0.0}

    def fn(t):
        freq = f0 + (f1 - f0) * t
        state["wob"] += 2.0 * math.pi * wobble / RATE
        freq *= 1.0 + 0.22 * math.sin(state["wob"])
        state["phase"] += freq / RATE
        return math.sin(state["phase"] * 2.0 * math.pi) * (1.0 - t) ** 1.2

    return _seq(ms, fn, vol)


def _mix(*tracks):
    n = max(len(t) for t in tracks)
    out = array.array("h", bytes(2 * n))
    for track in tracks:
        for i, value in enumerate(track):
            mixed = out[i] + value
            out[i] = max(-32767, min(32767, mixed))
    return out


def _jingle():
    parts = []
    gap = array.array("h", bytes(2 * int(RATE * 0.03)))
    for freq, ms in ((523, 110), (659, 110), (784, 220)):
        parts.append(_square(freq, freq, ms, vol=0.16))
        parts.append(gap)
    out = array.array("h")
    for part in parts:
        out.extend(part)
    return out


class Sfx:
    """Retro blips and boings: shoot, hit, wall boings, tick, win jingle."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(12)
            self.enabled = True
        except Exception:
            return
        raw = {
            "shoot": _mix(_square(860, 430, 80, vol=0.13)),
            "hit": _mix(_noise(150, vol=0.3), _square(280, 940, 120, vol=0.2)),
            "wall": _mix(_noise(40, vol=0.07)),
            "bounce": _mix(_square(180, 160, 40, vol=0.06)),
            # rubber wall boings - two pitches so repeats don't sound canned
            "boing": [_boing(560, 150, 150, 30.0, vol=0.11),
                      _boing(470, 130, 165, 24.0, vol=0.11)],
            "boing_low": _boing(300, 60, 260, 18.0, vol=0.16),
            "tick": _mix(_square(660, 660, 80, vol=0.13)),
            "start": _mix(_square(440, 880, 160, vol=0.15)),
            "select": _mix(_square(500, 500, 45, vol=0.09)),
            "win": _jingle(),
        }
        for name, data in raw.items():
            try:
                if isinstance(data, list):
                    self.sounds[name] = [pygame.mixer.Sound(buffer=d.tobytes())
                                         for d in data]
                else:
                    self.sounds[name] = pygame.mixer.Sound(buffer=data.tobytes())
            except Exception:
                self.enabled = False
                return

    def play(self, name):
        if self.enabled and name in self.sounds:
            sound = self.sounds[name]
            try:
                if isinstance(sound, list):      # pitch variants, e.g. boings
                    sound = random.choice(sound)
                sound.play()
            except Exception:
                pass
