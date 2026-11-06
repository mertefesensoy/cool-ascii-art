"""Pulsing ASCII heart for the terminal.

A shaded heart beats in a "lub-dub" rhythm, glows on each beat, small hearts
float upward, stars twinkle, and a line of text fades in and out.

Run:  python pulse_heart.py            (any key or Ctrl+C quits)
      python pulse_heart.py --seconds 20
Needs a terminal with 24-bit colour and UTF-8 (Windows Terminal works).
"""
import math
import os
import random
import shutil
import sys
import time

try:
    import msvcrt  # Windows console: lets any key close the animation
except ImportError:
    msvcrt = None


def key_pressed():
    """True once any key has been pressed (Windows console only)."""
    if msvcrt is not None and msvcrt.kbhit():
        while msvcrt.kbhit():
            msvcrt.getwch()
        return True
    return False


FPS = 20
BEAT_PERIOD = 1.05            # seconds per heartbeat
ASPECT = 1.85                 # terminal cell height / width

# Classic parametric heart: x = 16 sin^3 t, y = 13 cos t - 5 cos 2t - 2 cos 3t - cos 4t.
# Spans x in [-16, 16], y in [-17, ~12]; the centre top dips to y = 5.
HEART = [(16 * math.sin(a) ** 3,
          13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
         for a in (i * math.tau / 360 for i in range(360))]
HEART_MID = -2.5              # vertical centre of the shape in heart units
HEART_HEIGHT = 29.0


def heart_spans(y):
    """Inside intervals [(x0, x1), ...] of the heart on the horizontal line y."""
    xs = []
    n = len(HEART)
    for i in range(n):
        x0, y0 = HEART[i]
        x1, y1 = HEART[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return [(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)]
RAMP = " .:-=+*#%@"           # light to dense
MESSAGE = "♥  you & me, always  ♥"
BG = (14, 6, 20)              # deep plum background


def heartbeat(t):
    """Two quick bumps per period (lub-dub), 0..~1."""
    ph = (t % BEAT_PERIOD) / BEAT_PERIOD
    return math.exp(-((ph - 0.10) / 0.055) ** 2) + 0.65 * math.exp(-((ph - 0.30) / 0.06) ** 2)


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def scale_rgb(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def fg(c):
    return f"\x1b[38;2;{c[0]};{c[1]};{c[2]}m"


class Floater:
    def __init__(self, cols, rows):
        self.x = random.uniform(2, cols - 3)
        self.y = rows + random.uniform(0, 4)
        self.speed = random.uniform(4.0, 9.0)       # rows per second
        self.sway = random.uniform(0.6, 2.2)
        self.phase = random.uniform(0, math.tau)
        self.char = random.choice(["♥", "♥", "♡", "❤"])
        self.tint = random.choice([(255, 120, 170), (255, 80, 120), (255, 170, 200), (230, 90, 160)])

    def step(self, dt):
        self.y -= self.speed * dt
        self.phase += dt * 2.2

    def pos(self):
        return int(round(self.x + math.sin(self.phase) * self.sway)), int(round(self.y))


def main():
    seconds = None
    if "--seconds" in sys.argv:
        seconds = float(sys.argv[sys.argv.index("--seconds") + 1])

    os.system("")  # enables ANSI escape handling on Windows consoles
    out = sys.stdout
    try:
        out.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    out.write("\x1b[?1049h\x1b[?25l")  # alternate screen, hide cursor

    random.seed()
    stars, floaters = [], []
    star_size = (0, 0)
    t0 = last = time.time()
    try:
        while True:
            now = time.time()
            t, dt = now - t0, now - last
            last = now
            if (seconds is not None and t > seconds) or key_pressed():
                break
            cols, rows = shutil.get_terminal_size((120, 40))
            if (cols, rows) != star_size:
                star_size = (cols, rows)
                stars = [(random.randrange(cols), random.randrange(rows), random.uniform(0, math.tau),
                          random.uniform(0.8, 2.5)) for _ in range(max(12, cols * rows // 90))]

            beat = heartbeat(t)
            scale = 1.0 + 0.10 * beat
            base_unit = min(rows * 0.58 / HEART_HEIGHT, cols * 0.70 / (32 * ASPECT))  # rows per heart unit
            unit = base_unit * scale
            cx, cy = cols / 2.0, rows * 0.44

            # Grid of (char, rgb) on the background.
            grid = [[(" ", BG)] * cols for _ in range(rows)]

            # Twinkling stars.
            for sx, sy, ph, sp in stars:
                tw = 0.5 + 0.5 * math.sin(t * sp + ph)
                if tw > 0.35:
                    ch = "✦" if tw > 0.93 else ("*" if tw > 0.75 else "·")
                    grid[sy][sx] = (ch, mix(BG, (200, 180, 255), tw * 0.8))

            # Floating hearts rise from the bottom.
            if random.random() < 0.18 + 0.5 * beat * dt * FPS / 10:
                floaters.append(Floater(cols, rows))
            for f in floaters:
                f.step(dt)
            floaters = [f for f in floaters if f.y > -2]
            for f in floaters:
                x, y = f.pos()
                if 0 <= x < cols and 0 <= y < rows:
                    fade = max(0.25, min(1.0, y / (rows * 0.8)))
                    grid[y][x] = (f.char, mix(BG, f.tint, fade))

            # The heart, rasterised row by row from the parametric outline.
            glow_scale = 1.07 + 0.10 * beat
            top = max(0, int(cy - (12 - HEART_MID) * unit * glow_scale) - 1)
            bottom = min(rows, int(cy + (HEART_MID + 17) * unit * glow_scale) + 2)
            for r in range(top, bottom):
                y = HEART_MID + (cy - r) / unit
                spans = heart_spans(y)
                glow_spans = heart_spans(HEART_MID + (y - HEART_MID) / glow_scale)
                lo = min([s[0] for s in spans + [(s[0] * glow_scale, 0) for s in glow_spans]] or [0])
                hi = max([s[1] for s in spans + [(0, s[1] * glow_scale) for s in glow_spans]] or [0])
                c0 = max(0, int(cx + lo * unit * ASPECT) - 1)
                c1 = min(cols, int(cx + hi * unit * ASPECT) + 2)
                for c in range(c0, c1):
                    x = (c - cx) / (unit * ASPECT)
                    inside = next((s for s in spans if s[0] <= x <= s[1]), None)
                    if inside:
                        edge = min(x - inside[0], inside[1] - x)                 # heart units to the side edge
                        body = min(1.0, edge / 3.2)
                        shade = 1.0 - 0.35 * min(1.0, abs(y - 3.0) / 16.0)      # darker toward the tip
                        shine = math.exp(-((x + 7.0) ** 2 / 14.0 + (y - 6.5) ** 2 / 8.0))
                        light = min(1.0, 0.30 + 0.70 * body * shade + 0.6 * shine)
                        ch = RAMP[max(3, min(len(RAMP) - 1, int(light * (len(RAMP) - 1))))]
                        base = mix((190, 8, 50), (255, 90, 150), max(0.0, min(1.0, (y + 17.0) / 29.0)))
                        col = scale_rgb(base, 0.75 + 0.35 * beat)
                        col = mix(col, (255, 236, 246), shine * 0.85)
                        grid[r][c] = (ch, col)
                    else:
                        gx = x / glow_scale
                        if any(s[0] <= gx <= s[1] for s in glow_spans):
                            grid[r][c] = (":" if beat > 0.5 else "·",
                                          mix(BG, (255, 70, 140), 0.25 + 0.45 * beat))

            # Message under the heart, letters fading in a wave.
            mr = int(cy + (HEART_MID + 17) * base_unit * 1.2) + 2
            if 0 <= mr < rows:
                start = int(cx - len(MESSAGE) / 2)
                for i, ch in enumerate(MESSAGE):
                    c = start + i
                    if 0 <= c < cols and ch != " ":
                        wave = 0.55 + 0.45 * math.sin(t * 2.0 - i * 0.35)
                        grid[mr][c] = (ch, mix(BG, (255, 190, 215), wave))

            # Render: position each row explicitly, emit colour only on change.
            parts = [f"\x1b[48;2;{BG[0]};{BG[1]};{BG[2]}m"]
            for r in range(rows):
                parts.append(f"\x1b[{r + 1};1H")
                prev = None
                for ch, col in grid[r]:
                    if col != prev:
                        parts.append(fg(col))
                        prev = col
                    parts.append(ch)
            out.write("".join(parts))
            out.flush()
            time.sleep(max(0.0, 1.0 / FPS - (time.time() - now)))
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()


if __name__ == "__main__":
    main()
