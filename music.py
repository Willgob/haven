"""Procedural chiptune soundtrack - loops rendered to raw PCM at startup.

No audio files, no extra dependencies: every track is a small step-sequenced
composition (square lead, triangle bass, sine pads, noise drums) baked into a
looping buffer, matching the retro arcade look of the game.

Tracks:
    menu    - bouncy, melodic, mellow mix so UI blips cut through
    game    - driving bass + noise drums
    hurry   - same tune, double-time hats and extra snare for the final 10s
    pause   - low-pass "muffled" copy of the game loop (frozen-arena feel)
    results - calm victory loop that the win jingle leads into
"""

import array
import math
import os
import random

import pygame

RATE = 22050
STEPS_PER_BAR = 16

TAU = math.pi * 2.0


# --------------------------------------------------------------- wave shapes
def _square(ph):
    return 1.0 if (ph % 1.0) < 0.5 else -1.0


def _tri(ph):
    p = ph % 1.0
    return (4.0 * p - 1.0) if p < 0.5 else (3.0 - 4.0 * p)


def _sine(ph):
    return math.sin(ph * TAU)


WAVES = {"square": _square, "tri": _tri, "sine": _sine}


def _midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


# ------------------------------------------------------------------ rendering
def _render_note(buf, start, nsamp, freq, wave, vol, decay=1.3):
    """Add one enveloped note into the mix buffer (clamped accumulation)."""
    n = len(buf)
    if nsamp <= 2 or start >= n:
        return
    end = min(n, start + nsamp)
    attack_samp = max(1, int(0.004 * RATE))
    decay_samp = max(1, nsamp - attack_samp)
    wf = WAVES[wave]
    phase = 0.0
    inc = freq / RATE
    amp = 32767.0 * vol
    for i in range(start, end):
        k = i - start
        if k < attack_samp:
            env = k / attack_samp
        else:
            u = (k - attack_samp) / decay_samp
            env = (1.0 - u) ** decay
        value = buf[i] + int(wf(phase) * env * amp)
        buf[i] = -32768 if value < -32768 else (32767 if value > 32767 else value)
        phase += inc


def _render_kick(buf, start, vol):
    n = int(0.09 * RATE)
    phase = 0.0
    amp = 32767.0 * vol
    for i in range(n):
        idx = start + i
        if idx >= len(buf):
            break
        t = i / n
        freq = 130.0 * (1.0 - t) + 40.0
        phase += freq / RATE
        env = (1.0 - t) ** 1.5
        value = buf[idx] + int(math.sin(phase * TAU) * env * amp)
        buf[idx] = -32768 if value < -32768 else (32767 if value > 32767 else value)


def _render_snare(buf, start, vol):
    n = int(0.07 * RATE)
    phase = 0.0
    amp = 32767.0 * vol
    for i in range(n):
        idx = start + i
        if idx >= len(buf):
            break
        t = i / n
        env = (1.0 - t) ** 1.2
        tone = 1.0 if (phase % 1.0) < 0.5 else -1.0
        phase += 185.0 / RATE
        value = buf[idx] + int((random.uniform(-1, 1) * 0.8 + tone * 0.2) * env * amp)
        buf[idx] = -32768 if value < -32768 else (32767 if value > 32767 else value)


def _render_hat(buf, start, vol):
    n = int(0.022 * RATE)
    amp = 32767.0 * vol
    for i in range(n):
        idx = start + i
        if idx >= len(buf):
            break
        t = i / n
        value = buf[idx] + int(random.uniform(-1, 1) * (1.0 - t) * amp)
        buf[idx] = -32768 if value < -32768 else (32767 if value > 32767 else value)


def _render_track(notes, drums, tempo, bars=4):
    """notes: (bar, step, len_steps, midi, wave, vol)  drums: (bar, step, kind, vol)"""
    step_seconds = (60.0 / tempo) / 4.0          # 16th notes
    total = int(RATE * step_seconds * STEPS_PER_BAR * bars) + 64
    buf = array.array("h", bytes(2 * total))

    def step_sample(bar, step):
        return int((bar * STEPS_PER_BAR + step) * step_seconds * RATE)

    for bar, step, length, midi, wave, vol in notes:
        nsamp = int(length * step_seconds * RATE) - 40   # tiny gap = no clicks
        _render_note(buf, step_sample(bar, step), nsamp, _midi_to_freq(midi), wave, vol)
    for bar, step, kind, vol in drums:
        start = step_sample(bar, step)
        if kind == "kick":
            _render_kick(buf, start, vol)
        elif kind == "snare":
            _render_snare(buf, start, vol)
        else:
            _render_hat(buf, start, vol)
    return buf


def _lowpass(data, alpha=0.18):
    """One-pole low pass - turns the game loop into the muffled 'pause' mix."""
    out = array.array("h", bytes(2 * len(data)))
    prev = 0
    for i, value in enumerate(data):
        prev += alpha * (value - prev)
        out[i] = int(max(-32768, min(32767, prev)))
    return out


# ------------------------------------------------------------------ composing
def _build_menu():
    """Bouncy C major loop: I - vi - IV - V, octave-bouncing bass."""
    roots = (36, 45, 41, 43)                     # C2  A2  F2  G2
    notes = []
    bass = ((0, 1), (2, 1), (4, 1, 12), (6, 1), (8, 1),
            (10, 1, 12), (12, 1), (14, 1, 7))
    for bar, root in enumerate(roots):
        for entry in bass:
            step, length = entry[0], entry[1]
            off = entry[2] if len(entry) > 2 else 0
            notes.append((bar, step, length, root + off, "tri", 0.13))
    lead = (
        (0, 0, 2, 72), (0, 3, 1, 76), (0, 4, 2, 79), (0, 8, 1, 76), (0, 10, 2, 72), (0, 14, 1, 74),
        (1, 0, 2, 81), (1, 3, 1, 79), (1, 4, 2, 76), (1, 8, 1, 72), (1, 10, 2, 69), (1, 14, 1, 67),
        (2, 0, 2, 77), (2, 3, 1, 81), (2, 4, 2, 84), (2, 8, 1, 81), (2, 10, 2, 77), (2, 14, 1, 76),
        (3, 0, 2, 79), (3, 3, 1, 83), (3, 4, 2, 79), (3, 8, 1, 74), (3, 10, 2, 71), (3, 14, 2, 67),
    )
    for bar, step, length, midi in lead:
        notes.append((bar, step, length, midi, "square", 0.085))
    for bar, root in enumerate(roots):           # soft pluck on each downbeat
        notes.append((bar, 0, 2, root + 12, "tri", 0.05))
    drums = []
    for bar in range(4):
        for step in (0, 8):
            drums.append((bar, step, "kick", 0.14))
        for step in (0, 4, 8, 12):
            drums.append((bar, step, "hat", 0.04))
    return notes, drums, 128


def _build_game(hurry=False):
    """Driving A minor loop: Am - F - C - G. Hurry = double-time drums, hotter."""
    tempo = 148 if hurry else 138
    roots = (45, 41, 36, 43)                     # A2  F2  C2  G2
    notes = []
    for bar, root in enumerate(roots):
        for step in range(0, 16, 2):             # straight driving 8ths
            off = 0
            if step in (6, 14):
                off = 12                          # octave kick
            elif step == 12:
                off = 7                           # fifth push
            notes.append((bar, step, 1, root + off, "tri", 0.14))
    lead = (
        (0, 0, 1, 69), (0, 2, 1, 72), (0, 3, 1, 76), (0, 4, 2, 79), (0, 8, 1, 76), (0, 10, 1, 72), (0, 12, 2, 69),
        (1, 0, 1, 69), (1, 2, 1, 72), (1, 3, 1, 77), (1, 4, 2, 81), (1, 8, 1, 77), (1, 10, 1, 72), (1, 12, 2, 69),
        (2, 0, 1, 72), (2, 2, 1, 76), (2, 3, 1, 79), (2, 4, 2, 84), (2, 8, 1, 79), (2, 10, 1, 76), (2, 12, 2, 72),
        (3, 0, 1, 74), (3, 2, 1, 79), (3, 3, 1, 83), (3, 4, 2, 79), (3, 8, 1, 74), (3, 10, 1, 71), (3, 12, 2, 74),
    )
    for bar, step, length, midi in lead:
        notes.append((bar, step, length, midi, "square", 0.11 if not hurry else 0.12))
    drums = []
    for bar in range(4):
        for step in (0, 8):
            drums.append((bar, step, "kick", 0.16))
        for step in (4, 12):
            drums.append((bar, step, "snare", 0.11))
        hat_vol = 0.055 if hurry else 0.05
        for step in range(0, 16, 1 if hurry else 2):
            drums.append((bar, step, "hat", hat_vol))
        if hurry:
            for step in (2, 6, 10, 14):
                drums.append((bar, step, "snare", 0.05))
    return notes, drums, tempo


def _build_results():
    """Calm C major loop in the same key as the win jingle (C-E-G)."""
    tempo = 92
    roots = (36, 43, 45, 41)                     # C2  G2  A2  F2
    thirds = (4, 4, 3, 4)                        # major third except Am
    notes = []
    for bar, root in enumerate(roots):
        third = thirds[bar]
        notes.append((bar, 0, 16, root + 12, "sine", 0.05))
        notes.append((bar, 0, 16, root + 12 + third, "sine", 0.045))
        notes.append((bar, 0, 16, root + 19, "sine", 0.04))
        arp = (root + 12, root + 19, root + 24, root + 19)
        for idx, step in enumerate(range(0, 16, 2)):
            notes.append((bar, step, 1, arp[idx % 4], "tri", 0.06))
    drums = []
    for bar in range(4):
        drums.append((bar, 0, "kick", 0.09))
        drums.append((bar, 8, "hat", 0.03))
    return notes, drums, tempo


# ---------------------------------------------------------------------- mixer
TRACK_VOLUMES = {"menu": 0.32, "game": 0.40, "hurry": 0.42, "pause": 0.26, "results": 0.30}

# In-game music file (looped during matches). If it is missing or cannot be
# decoded, the game quietly falls back to the built-in chiptune loop.
INGAME_MP3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "seels.mp3")
INGAME_VOLUME = 0.30          # the mp3 is mastered much louder than the synth loops
HURRY_SPEED = 1.12            # final 10s: same song played a bit faster / higher

# Other mp3 tracks: name -> (file in assets/, volume, loops). loops=-1 repeats
# forever, 0 plays once. A missing file just keeps the built-in chiptune track.
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
FILE_TRACKS = {
    "menu": ("menu.mp3", 0.28, -1),          # main menu: Retro Platforming
    "results": ("victory.mp3", 0.55, 0),     # results screen: victory fanfare, once
}
TRACK_LOOPS = {}


def _resample(data, speed):
    """Linear-interpolation resample of mono 16-bit PCM; speed > 1 = faster + higher."""
    n = int(len(data) / speed)
    out = array.array("h", bytes(2 * n))
    last = len(data) - 1
    for i in range(n):
        pos = i * speed
        j = int(pos)
        a = data[j]
        b = data[j + 1 if j < last else last]
        out[i] = int(a + (b - a) * (pos - j))
    return out


def _load_ingame_pcm():
    """Decode the in-game mp3 via the mixer; returns (Sound, mono 16-bit PCM or None)."""
    if not os.path.isfile(INGAME_MP3):
        return None, None
    sound = pygame.mixer.Sound(INGAME_MP3)
    _freq, size, channels = pygame.mixer.get_init()
    pcm = None
    if size == -16 and channels == 1:         # processing below assumes mono 16-bit
        pcm = array.array("h", sound.get_raw())
    return sound, pcm


class Music:
    """Looping chiptune tracks on a reserved mixer channel."""

    def __init__(self):
        self.enabled = False
        self.current = None
        self.tracks = {}
        if pygame.mixer.get_init() is None:
            return                                # mixer never came up - stay silent
        try:
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.channel = pygame.mixer.Channel(0)
            game_buf = _render_track(*_build_game(False))
            self.tracks = {
                "menu": pygame.mixer.Sound(buffer=_render_track(*_build_menu()).tobytes()),
                "game": pygame.mixer.Sound(buffer=game_buf.tobytes()),
                "hurry": pygame.mixer.Sound(buffer=_render_track(*_build_game(True)).tobytes()),
                "pause": pygame.mixer.Sound(buffer=_lowpass(game_buf).tobytes()),
                "results": pygame.mixer.Sound(buffer=_render_track(*_build_results()).tobytes()),
            }
            self._use_ingame_mp3()
            self._use_file_tracks()
            self.enabled = True
        except Exception:
            self.enabled = False
            self.tracks = {}

    def _use_ingame_mp3(self):
        """Swap the match tracks for the mp3 (plus muffled pause / fast hurry mixes)."""
        try:
            sound, pcm = _load_ingame_pcm()
            if sound is None:
                return                            # no file: keep the chiptune loops
            self.tracks["game"] = sound
            if pcm is not None:
                self.tracks["pause"] = pygame.mixer.Sound(buffer=_lowpass(pcm).tobytes())
                self.tracks["hurry"] = pygame.mixer.Sound(
                    buffer=_resample(pcm, HURRY_SPEED).tobytes())
            TRACK_VOLUMES["game"] = INGAME_VOLUME
            TRACK_VOLUMES["hurry"] = INGAME_VOLUME + 0.03
            TRACK_VOLUMES["pause"] = INGAME_VOLUME * 0.7
        except Exception:
            pass                                  # any problem: chiptune stays in place

    def _use_file_tracks(self):
        """Swap in the menu / victory mp3s; each one falls back on its own."""
        for name, (filename, volume, loops) in FILE_TRACKS.items():
            path = os.path.join(_ASSETS, filename)
            try:
                if not os.path.isfile(path):
                    continue
                self.tracks[name] = pygame.mixer.Sound(path)
                TRACK_VOLUMES[name] = volume
                TRACK_LOOPS[name] = loops
            except Exception:
                pass                              # keep the chiptune for this track

    def play(self, name, fade_ms=90):
        """Switch loops smoothly; no-ops when the requested track is already on."""
        if not self.enabled or name == self.current:
            return
        sound = self.tracks.get(name)
        if sound is None:
            return
        self.channel.fadeout(130)
        self.channel.set_volume(TRACK_VOLUMES.get(name, 0.35))
        self.channel.play(sound, loops=TRACK_LOOPS.get(name, -1), fade_ms=fade_ms)
        self.current = name

    def stop(self, fade_ms=250):
        if self.enabled:
            self.channel.fadeout(fade_ms)
        self.current = None
