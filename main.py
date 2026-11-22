#!/usr/bin/env python3
"""The World Today -- Sunday 22 November 2026.

Draws a one-page newspaper front page (1024 x 1024 PNG) summing up the
world news of Sunday 22 November 2026.

Pure standard library. No network, no file reads at run time: every pixel
and every letterform is computed from data inside this file. The PNG
binary is built by hand (struct + zlib).

Usage:
    MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
Writes entry.png into that directory (or ./out when the variable is unset).
Deterministic: repeated runs produce byte-identical output.
"""

import os
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)      # off-white newsprint
INK = (17, 17, 17)           # near-black ink
ACCENT = (176, 32, 32)       # restrained red (masthead + fire)
SKY_TOP = (34, 50, 66)
SKY_LOW = (58, 80, 100)
SEA = (15, 40, 62)
SEA_LINE = (48, 94, 124)
HULL = (24, 24, 26)
SUPER = (232, 230, 224)
FLAME = (255, 110, 20)
FLAME_HOT = (255, 196, 40)
SMOKE = (72, 74, 80)
SMOKE_LIGHT = (112, 114, 120)
WHITE = (255, 255, 255)
GREY = (120, 116, 108)

# ------------------------------------------------------------------- font
# 5x7 bitmap letterforms. Each glyph is 7 rows of 5 characters;
# '1' is ink, '0' is empty. Covers A-Z, 0-9 and common punctuation.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "00100", "00100", "00100", "00100", "00010"),
    ')': ("01000", "00100", "00100", "00100", "00100", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10010", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '=': ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    '*': ("00000", "01010", "01110", "11111", "01110", "01010", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '$': ("00100", "01111", "10101", "01110", "00101", "10101", "11100"),
    '@': ("01110", "10001", "10111", "10101", "10111", "10000", "01110"),
}


def char_advance(scale):
    """Horizontal advance of one glyph cell at the given scale."""
    return 6 * scale


def text_width(text, scale, advance=None):
    if advance is None:
        advance = char_advance(scale)
    if not text:
        return 0
    return len(text) * advance - (advance - 5 * scale)


# ----------------------------------------------------------------- canvas
class Canvas(object):
    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.buf = bytearray(bytes(background) * (width * height))

    def _clip(self, x, y, w, h):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        return x0, y0, x1, y1

    def fill_rect(self, x, y, w, h, color):
        x0, y0, x1, y1 = self._clip(x, y, w, h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        stride = self.width * 3
        for yy in range(y0, y1):
            off = yy * stride + x0 * 3
            self.buf[off:off + len(row)] = row

    def draw_rect(self, x, y, w, h, color, thickness=1):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            off = (y * self.width + x) * 3
            self.buf[off:off + 3] = bytes(color)

    def draw_line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_polygon(self, points, color):
        ys = [p[1] for p in points]
        y0, y1 = min(ys), max(ys)
        n = len(points)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = points[i]
                x2, y2p = points[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(round(xs[i]))
                xb = int(round(xs[i + 1]))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, color)

    # ------------------------------------------------------------- text
    def draw_text(self, text, x, y, scale, color, advance=None):
        if advance is None:
            advance = char_advance(scale)
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT['?']
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += advance
        return cx

    def draw_text_centered(self, text, cx, y, scale, color, advance=None):
        w = text_width(text, scale, advance)
        self.draw_text(text, cx - w // 2, y, scale, color, advance)

    def wrap_text(self, text, max_width, scale, advance=None):
        """Greedy word wrap; returns a list of lines."""
        if advance is None:
            advance = char_advance(scale)
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            cur = ''
            for word in words:
                trial = word if not cur else cur + ' ' + word
                if text_width(trial, scale, advance) <= max_width or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines


# ----------------------------------------------------------------- layout
MARGIN = 24
CONTENT_W = WIDTH - 2 * MARGIN  # 976


def draw_masthead(c):
    # Accent rule across the very top.
    c.fill_rect(0, 0, WIDTH, 8, ACCENT)
    # Newspaper name, large.
    c.draw_text_centered("THE WORLD TODAY", WIDTH // 2, 24, 6, INK)
    # Date, large and unmissable, in the accent colour.
    c.draw_text_centered("SUNDAY 22 NOVEMBER 2026", WIDTH // 2, 80, 4, ACCENT)
    # Tagline.
    c.draw_text_centered("ONE DAY. ONE PAGE.", WIDTH // 2, 116, 2, INK)
    # Double rule under the masthead.
    c.fill_rect(MARGIN, 138, CONTENT_W, 2, INK)
    c.fill_rect(MARGIN, 144, CONTENT_W, 2, INK)


def draw_drone(c, cx, cy):
    # Small quad-rotor drone: dark body, four rotor arms, one red light.
    c.fill_rect(cx - 7, cy - 2, 14, 4, INK)
    c.fill_rect(cx - 12, cy - 5, 24, 2, INK)
    c.fill_rect(cx - 12, cy - 5, 2, 2, INK)
    c.fill_rect(cx + 10, cy - 5, 2, 2, INK)
    c.fill_rect(cx - 1, cy + 2, 2, 4, INK)
    c.set_pixel(cx + 5, cy, ACCENT)
    c.set_pixel(cx + 6, cy, ACCENT)


def draw_ship_scene(c, x0, y0, x1, y1):
    """Baltic Sea hero scene inside the box (x0, y0) - (x1, y1)."""
    # Sky: two flat bands.
    c.fill_rect(x0, y0, x1 - x0, 66, SKY_TOP)
    c.fill_rect(x0, y0 + 66, x1 - x0, 46, SKY_LOW)
    # A few pale stars in the dark sky.
    for sx, sy in ((90, y0 + 14), (180, y0 + 34), (905, y0 + 18),
                   (960, y0 + 44), (60, y0 + 52), (700, y0 + 12)):
        c.fill_rect(sx, sy, 2, 2, (200, 205, 210))
    # Drones in the sky.
    draw_drone(c, 330, y0 + 34)
    draw_drone(c, 620, y0 + 24)
    draw_drone(c, 830, y0 + 44)
    # Distant dark coastline on the left horizon.
    c.fill_polygon([(x0, y0 + 112), (240, y0 + 96), (330, y0 + 112),
                    (330, y0 + 118), (x0, y0 + 118)], (12, 24, 36))
    # Sea.
    c.fill_rect(x0, y0 + 112, x1 - x0, y1 - y0 - 112, SEA)
    # Wave strokes.
    for wx, wy, wl in ((60, y0 + 140, 70), (160, y0 + 168, 90),
                       (700, y0 + 150, 80), (850, y0 + 178, 90),
                       (120, y0 + 205, 60), (760, y0 + 215, 70),
                       (420, y0 + 225, 80), (920, y0 + 130, 50)):
        c.fill_rect(wx, wy, wl, 2, SEA_LINE)
        c.fill_rect(wx + 8, wy + 5, wl - 16, 2, SEA_LINE)

    # --- Cargo ship Sparta II, centre-left, burning mid-ship.
    hull_y = y0 + 182
    # Hull with a raked bow to the right.
    c.fill_polygon([(300, hull_y), (700, hull_y), (730, hull_y + 18),
                    (700, hull_y + 44), (300, hull_y + 44)], HULL)
    c.fill_rect(300, hull_y + 38, 400, 6, (120, 30, 30))
    # Containers on deck.
    for cx0, col in ((320, (46, 110, 120)), (372, (150, 70, 40)),
                     (424, (110, 110, 105)), (476, (46, 110, 120)),
                     (528, (150, 70, 40))):
        c.fill_rect(cx0, hull_y - 26, 48, 26, col)
        c.draw_rect(cx0, hull_y - 26, 48, 26, INK, 1)
    # White superstructure and red funnel.
    c.fill_rect(596, hull_y - 58, 72, 58, SUPER)
    c.draw_rect(596, hull_y - 58, 72, 58, INK, 1)
    for wy in (hull_y - 50, hull_y - 34, hull_y - 18):
        c.fill_rect(604, wy, 56, 6, (40, 60, 80))
    c.fill_rect(672, hull_y - 68, 22, 68, ACCENT)
    c.fill_rect(672, hull_y - 68, 22, 10, INK)
    # Ship name on the hull.
    c.draw_text("SPARTA II", 330, hull_y + 12, 2, WHITE)
    # Flames rising from the mid-ship containers.
    c.fill_polygon([(430, hull_y - 26), (455, hull_y - 84),
                    (470, hull_y - 60), (490, hull_y - 96),
                    (505, hull_y - 62), (525, hull_y - 80),
                    (545, hull_y - 26)], FLAME)
    c.fill_polygon([(455, hull_y - 26), (470, hull_y - 62),
                    (482, hull_y - 44), (495, hull_y - 70),
                    (510, hull_y - 40), (520, hull_y - 26)], FLAME_HOT)
    # Smoke drifting up and left.
    for sx, sy, sr, col in ((470, hull_y - 96, 18, SMOKE),
                            (500, hull_y - 122, 22, SMOKE_LIGHT),
                            (532, hull_y - 146, 16, SMOKE),
                            (455, hull_y - 128, 14, SMOKE_LIGHT),
                            (512, hull_y - 168, 14, SMOKE)):
        c.fill_circle(sx, sy, sr, col)
    # Lifeboat with the evacuated crew, off the port side.
    c.fill_rect(170, hull_y + 26, 62, 14, (255, 130, 30))
    c.draw_rect(170, hull_y + 26, 62, 14, INK, 1)
    for px in (182, 196, 210, 222):
        c.fill_rect(px, hull_y + 18, 5, 8, INK)

    # --- Coast-guard vessel on the right, coming to help.
    gy = y0 + 196
    c.fill_polygon([(780, gy), (940, gy), (960, gy + 14),
                    (940, gy + 30), (780, gy + 30)], SUPER)
    c.draw_rect(780, gy, 180, 30, INK, 1)
    c.fill_rect(780, gy + 22, 160, 6, ACCENT)
    c.fill_rect(820, gy - 26, 52, 26, SUPER)
    c.draw_rect(820, gy - 26, 52, 26, INK, 1)
    c.fill_rect(840, gy - 20, 32, 6, (40, 60, 80))
    # Mast and a small Finnish flag (white, blue cross).
    c.fill_rect(892, gy - 48, 3, 48, INK)
    c.fill_rect(895, gy - 48, 26, 16, WHITE)
    c.fill_rect(903, gy - 48, 4, 16, (40, 90, 180))
    c.fill_rect(895, gy - 42, 26, 4, (40, 90, 180))
    # Scene caption, top left.
    c.draw_text("GULF OF FINLAND", x0 + 14, y0 + 12, 2, WHITE)


def draw_hero(c):
    top = 160
    bottom = 560
    c.draw_rect(MARGIN, top, CONTENT_W, bottom - top, INK, 3)
    # Headline band in ink with white letters.
    c.fill_rect(MARGIN + 3, top + 3, CONTENT_W - 6, 60, INK)
    c.draw_text_centered("BALTIC SEA ON FIRE", WIDTH // 2, top + 12, 6, WHITE)
    # Scene.
    draw_ship_scene(c, MARGIN + 3, top + 63, WIDTH - MARGIN - 3, 478)
    # Two-line sub-headline on paper.
    c.draw_text_centered("DRONES HIT THE RUSSIAN CARGO SHIP SPARTA II",
                         WIDTH // 2, 490, 3, INK, advance=16)
    c.draw_text_centered("FINLAND TIGHTENED SECURITY AS WAR SPILLS INTO NATO WATERS",
                         WIDTH // 2, 524, 3, INK, advance=16)


def draw_panel(c, x, w, label, headline_lines, sub_text, art):
    top = 576
    bottom = 800
    c.draw_rect(x, top, w, bottom - top, INK, 2)
    # Label band.
    c.fill_rect(x + 2, top + 2, w - 4, 28, ACCENT)
    c.draw_text_centered(label, x + w // 2, top + 8, 2, WHITE)
    # Headline lines, scale 3.
    hy = top + 42
    for line in headline_lines:
        c.draw_text(line, x + 12, hy, 3, INK)
        hy += 27
    # Sub-line, scale 2, wrapped.
    sy = hy + 8
    for line in c.wrap_text(sub_text, w - 24, 2):
        c.draw_text(line, x + 12, sy, 2, INK)
        sy += 20
    # Small illustration at the bottom of the panel.
    art(c, x, top, w, bottom)


def art_climate(c, x, top, w, bottom):
    cx = x + w // 2
    cy = bottom - 46
    # Rising sun with rays behind the globe.
    c.fill_circle(cx + 34, cy - 34, 10, FLAME_HOT)
    for dx, dy in ((0, -18), (13, -13), (18, 0), (13, 13)):
        c.fill_rect(cx + 34 + dx - 2, cy - 34 + dy - 2, 4, 4, FLAME_HOT)
    # Globe: blue sea, green land blobs.
    c.fill_circle(cx, cy, 30, (40, 110, 170))
    c.fill_polygon([(cx - 20, cy - 8), (cx - 6, cy - 16), (cx + 2, cy - 4),
                    (cx - 8, cy + 6), (cx - 22, cy + 4)], (70, 160, 80))
    c.fill_polygon([(cx + 8, cy + 4), (cx + 20, cy - 2), (cx + 22, cy + 12),
                    (cx + 10, cy + 18)], (70, 160, 80))
    # Latitude lines.
    c.fill_rect(cx - 28, cy - 10, 56, 2, (160, 200, 230))
    c.fill_rect(cx - 30, cy + 8, 60, 2, (160, 200, 230))


def art_gulf(c, x, top, w, bottom):
    cx = x + w // 2
    hy = bottom - 44
    # Tanker silhouette.
    c.fill_polygon([(cx - 95, hy), (cx + 85, hy), (cx + 105, hy + 12),
                    (cx + 85, hy + 24), (cx - 95, hy + 24)], HULL)
    for tx in (cx - 82, cx - 42, cx - 2):
        c.fill_circle(tx + 16, hy - 8, 13, (150, 70, 40))
    c.fill_rect(cx + 58, hy - 22, 22, 22, SUPER)
    # Flame bursting from the struck tank, with a hot core and smoke,
    # so the hit reads clearly at a glance.
    c.fill_polygon([(cx - 34, hy), (cx - 26, hy - 30), (cx - 18, hy - 14),
                    (cx - 10, hy - 34), (cx - 2, hy - 12), (cx + 6, hy - 24),
                    (cx + 10, hy)], FLAME)
    c.fill_polygon([(cx - 24, hy), (cx - 18, hy - 20), (cx - 12, hy - 8),
                    (cx - 6, hy - 18), (cx, hy)], FLAME_HOT)
    c.fill_circle(cx - 10, hy - 42, 7, SMOKE)
    # Waves.
    for wx in (cx - 105, cx - 55, cx, cx + 55):
        c.fill_rect(wx, hy + 32, 42, 2, SEA_LINE)


def art_flags(c, x, top, w, bottom):
    fy = bottom - 62
    # US flag: stripes + blue canton.
    ux = x + 28
    for i in range(4):
        c.fill_rect(ux, fy + i * 9, 96, 5, ACCENT if i % 2 == 0 else WHITE)
    c.fill_rect(ux, fy, 40, 18, (40, 60, 140))
    c.draw_rect(ux, fy, 96, 36, INK, 1)
    # Canadian flag: red-white-red with a red diamond leaf.
    kx = x + w - 124
    c.fill_rect(kx, fy, 24, 36, ACCENT)
    c.fill_rect(kx + 24, fy, 48, 36, WHITE)
    c.fill_rect(kx + 72, fy, 24, 36, ACCENT)
    c.fill_polygon([(kx + 48, fy + 6), (kx + 56, fy + 16), (kx + 52, fy + 20),
                    (kx + 58, fy + 26), (kx + 48, fy + 30), (kx + 38, fy + 26),
                    (kx + 44, fy + 20), (kx + 40, fy + 16)], ACCENT)
    c.draw_rect(kx, fy, 96, 36, INK, 1)
    # A thin divider between the two flags.
    c.fill_rect(x + w // 2 - 1, fy + 4, 2, 28, GREY)


def draw_panels(c):
    pw = 320
    gap = 8
    draw_panel(c, MARGIN, pw, "COP31",
               ["CLIMATE TALKS", "DEADLOCK"],
               "Talks in overtime with no deal on fossil fuels.",
               art_climate)
    draw_panel(c, MARGIN + pw + gap, pw, "GULF",
               ["GULF ON EDGE"],
               "Tankers hit off Oman as US-Iran tensions rise.",
               art_gulf)
    draw_panel(c, MARGIN + 2 * (pw + gap), pw, "US-CANADA",
               ["PENTAGON CURBS", "US-CANADA TIES"],
               "Defence secretary limited military contacts with Ottawa.",
               art_flags)


TICKER_ITEMS = (
    "Magnitude 6.9 earthquake shook Peru's Andes; no damage reported.",
    "Brazil's ex-president Bolsonaro in intensive care in Brasilia.",
    "Australia broke England's seven-match T20 winning streak.",
    "AI may have helped solve a famous maths problem.",
    "Cyclone Akvan forced flight cancellations in India.",
)


def draw_ticker(c):
    top = 816
    # Header with an accent square.
    c.fill_rect(MARGIN, top + 2, 12, 12, ACCENT)
    c.draw_text("ALSO IN THE NEWS", MARGIN + 20, top, 2, INK)
    c.fill_rect(MARGIN, top + 24, CONTENT_W, 2, INK)
    # Five short items, one line each, each with an accent bullet.
    y = top + 38
    for item in TICKER_ITEMS:
        c.fill_rect(MARGIN + 2, y + 4, 8, 8, ACCENT)
        c.draw_text(item.upper(), MARGIN + 20, y, 2, INK)
        y += 26
    # Double rule at the foot of the page.
    c.fill_rect(MARGIN, 1000, CONTENT_W, 2, INK)
    c.fill_rect(MARGIN, 1006, CONTENT_W, 2, INK)


def build_image():
    c = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(c)
    draw_hero(c)
    draw_panels(c)
    draw_ticker(c)
    return c.buf


# -------------------------------------------------------------------- png
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb):
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = WIDTH * 3
    for y in range(HEIGHT):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main(argv):
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build_image())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
