# ASCII terminal animations

Python 3, no packages needed. Use Windows Terminal (24-bit colour, UTF-8).

| Script | What it shows | Preview |
| --- | --- | --- |
| `pulse_heart.py` | Shaded ASCII heart beating lub-dub with a glow, floating hearts, twinkling stars, "♥ you & me, always ♥" | `previews/pulse_heart.gif` |
| `geri_donecegim_matrix.py` | Matrix digital rain that decodes into "GERİ DÖNECEĞİM", glitches, and types "> sistem: bağlantı koptu... geri döneceğim" | `previews/geri_donecegim_matrix.gif` |

## Use as an "away" screen

1. Double-click `geri_donecegim_fullscreen.cmd` (or `heart_fullscreen.cmd`). It opens full screen.
2. When you're back, press **any key**. The animation stops and the window closes.

Other ways to close it: **Alt+F4**, or **Ctrl+C**. If the window ever stays open after closing the animation, Alt+F4 closes it.

Tip: pin a launcher to the taskbar or copy it to the Desktop for one click.

**This does not lock your computer.** Anyone can press a key and use it. If that matters, lock with **Win+L** instead (the lock screen hides the animation).

## Run from a terminal

```
wt --fullscreen python pulse_heart.py
wt --fullscreen python geri_donecegim_matrix.py
```

Stop after N seconds: add `--seconds 20`.

## Notes

- `ASPECT` in `pulse_heart.py` (1.85) is the terminal cell height/width ratio; change it if the heart looks stretched in another font.
- The Matrix font is a 5x9 bitmap (`FONT`) with accent rows for İ, Ö, Ğ; add letters there to change the text.
