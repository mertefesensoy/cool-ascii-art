"""Matrix-style digital rain that decodes into "GERİ DÖNECEĞİM".

Green glyphs rain down; block letters resolve out of the rain, hold with a
soft glow, glitch now and then, and a terminal line types itself at the bottom.

Run:  python geri_donecegim_matrix.py            (any key or Ctrl+C quits)
      python geri_donecegim_matrix.py --seconds 20
Full screen on Windows:  wt --fullscreen python geri_donecegim_matrix.py
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


FPS = 22
TEXT = "GERİ DÖNECEĞİM"
TYPED = "> sistem: bağlantı koptu... geri döneceğim"
GLYPHS = [chr(c) for c in range(0xFF66, 0xFF9E)] + list("0123456789Z:.=*+-<>¦|")
BG = (0, 6, 2)

# 5x9 bitmap font: two accent rows on top, then the 7-row letter body.
FONT = {
    "G": ["     ", "     ", " ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "],
    "E": ["     ", "     ", "#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "R": ["     ", "     ", "#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "İ": ["     ", "  #  ", "#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"],
    "D": ["     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "Ö": ["     ", " # # ", " ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "N": ["     ", "     ", "#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "C": ["     ", "     ", " ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    "Ğ": ["#   #", " ### ", " ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "],
    "M": ["     ", "     ", "#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"],
    " ": ["     "] * 9,
}


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def text_layout(cols, rows):
    """Cells covered by the big text, as {(r, c): letter_index}."""
    lines = [TEXT]
    sx = max(1, int(cols * 0.88 // (len(TEXT) * 6)))
    if sx < 2:                                  # too narrow for one line at 2x: split in two
        lines = ["GERİ", "DÖNECEĞİM"]
        sx = max(1, int(cols * 0.88 // (max(len(l) for l in lines) * 6)))
    sy = max(1, min(sx, int(rows * 0.55 // (len(lines) * 11))))
    block_h = len(lines) * 10 * sy + (len(lines) - 1) * 2 * sy
    top = int(rows * 0.42 - block_h / 2)
    cells = {}
    idx = 0
    for li, line in enumerate(lines):
        width = len(line) * 6 * sx - sx
        left = int((cols - width) / 2)
        y0 = top + li * (12 * sy)
        for k, ch in enumerate(line):
            glyph = FONT.get(ch, FONT[" "])
            bmp = glyph[:2] + ["     "] + glyph[2:]   # one empty row between accent and letter
            for fr, row in enumerate(bmp):
                for fc, px in enumerate(row):
                    if px == "#":
                        for dy in range(sy):
                            for dx in range(sx):
                                r, c = y0 + fr * sy + dy, left + (k * 6 + fc) * sx + dx
                                if 0 <= r < rows and 0 <= c < cols:
                                    cells[(r, c)] = idx
            idx += 1
    return cells, top + block_h


class Drop:
    def __init__(self, rows, fresh=False):
        self.y = random.uniform(-rows, 0) if fresh else random.uniform(-rows * 0.5, -1)
        self.speed = random.uniform(10, 32)        # rows per second
        self.length = random.randint(6, 24)


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
    out.write("\x1b[?1049h\x1b[?25l")

    size = (0, 0)
    drops, chars, cells, reveal, text_bottom = [], [], {}, {}, 0
    t0 = last = time.time()
    try:
        while True:
            now = time.time()
            t, dt = now - t0, min(0.1, now - last)
            last = now
            if (seconds is not None and t > seconds) or key_pressed():
                break
            cols, rows = shutil.get_terminal_size((120, 40))
            if (cols, rows) != size:
                size = (cols, rows)
                drops = [Drop(rows, fresh=True) for _ in range(cols)]
                chars = [[random.choice(GLYPHS) for _ in range(cols)] for _ in range(rows)]
                cells, text_bottom = text_layout(cols, rows)
                reveal = {cell: 1.6 + random.uniform(0, 2.8) for cell in cells}

            # Cycle: rain alone, text decodes, holds; glitch bursts every ~6 s.
            cycle = t % 14.0
            glitch = (cycle % 6.0) < 0.35 and t > 6
            fade_out = cycle > 13.2

            grid = [[(" ", BG)] * cols for _ in range(rows)]

            # Mutate a few rain glyphs each frame.
            for _ in range(max(1, cols * rows // 60)):
                chars[random.randrange(rows)][random.randrange(cols)] = random.choice(GLYPHS)

            # Rain.
            for c, d in enumerate(drops):
                d.y += d.speed * dt
                head = int(d.y)
                if head - d.length > rows:
                    drops[c] = Drop(rows)
                    continue
                for k in range(d.length):
                    r = head - k
                    if 0 <= r < rows:
                        if k == 0:
                            col = (210, 255, 220)
                        else:
                            f = 1.0 - k / d.length
                            col = mix((0, 40, 12), (0, 255, 90), f * f)
                        grid[r][c] = (chars[r][c], col)

            # Big text decoding out of the rain.
            pulse = 0.5 + 0.5 * math.sin(t * 2.4)
            local = t % 14.0
            for (r, c), _i in cells.items():
                start = reveal[(r, c)]
                if local < start:
                    if local > start - 1.2:          # about to resolve: flicker random glyphs
                        grid[r][c] = (random.choice(GLYPHS), mix((0, 120, 40), (150, 255, 170), random.random()))
                    continue
                if fade_out:
                    k = (14.0 - local) / 0.8
                    grid[r][c] = ("█" if k > 0.5 else "▓", mix(BG, (60, 255, 120), k))
                elif glitch and random.random() < 0.35:
                    grid[r][c] = (random.choice(GLYPHS), (230, 255, 235))
                else:
                    settle = min(1.0, (local - start) / 0.4)
                    col = mix((210, 255, 220), mix((0, 210, 80), (90, 255, 140), pulse), settle)
                    grid[r][c] = ("█", col)

            # Typed terminal line near the bottom.
            tr = min(rows - 2, text_bottom + max(3, rows // 10))
            shown = int(max(0.0, local - 5.0) * 14)
            line = TYPED[:shown]
            cursor = "_" if int(t * 2.5) % 2 == 0 else " "
            start_c = max(1, int((cols - len(TYPED)) / 2))
            if 0 <= tr < rows and local > 4.5 and not fade_out:
                for i, ch in enumerate(line + cursor):
                    c = start_c + i
                    if 0 <= c < cols:
                        grid[tr][c] = (ch, (140, 255, 170) if ch != "_" else (210, 255, 220))

            parts = [f"\x1b[48;2;{BG[0]};{BG[1]};{BG[2]}m"]
            for r in range(rows):
                parts.append(f"\x1b[{r + 1};1H")
                prev = None
                for ch, col in grid[r]:
                    if col != prev:
                        parts.append(f"\x1b[38;2;{col[0]};{col[1]};{col[2]}m")
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
