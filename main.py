#!/usr/bin/env python3
"""THE WORLD TODAY — Wednesday 25 November 2026.

Draws a one-page newspaper broadsheet summarising the day's world news
(39 stories, 7 regions) as a 1024x1024 PNG, using only Pillow and the
system DejaVu fonts. No network, no randomness, no timestamps: two runs
produce byte-identical output.

Layout (1024 x 1024):
  masthead -> lead story -> illustrated world map with pins
  -> three secondary leads -> four region columns -> markets ticker
"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (250, 247, 240)
INK = (17, 17, 17)
RED = (178, 34, 34)
TEAL = (31, 92, 96)
TEAL_DK = (18, 64, 68)
GREY = (90, 86, 78)
LIGHT = (233, 229, 219)
MAP_BG = (214, 228, 226)
MAP_LAND = (96, 138, 130)
MAP_LINE = (180, 198, 194)

FD = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)      # noqa: E731
SERIF = lambda s: font("DejaVuSerif.ttf", s)             # noqa: E731
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)        # noqa: E731
SANS = lambda s: font("DejaVuSans.ttf", s)               # noqa: E731


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, max_w, fill=INK, leading=None):
    lines = wrap(draw, text, fnt, max_w)
    lh = leading or int(fnt.size * 1.28)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- continents
# Stylised lon/lat outlines (equirectangular), drawn inside the map panel.
CONTINENTS = [
    # North America
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-110, 68), (-95, 69),
     (-90, 66), (-85, 66), (-80, 73), (-75, 62), (-68, 58), (-60, 55),
     (-55, 52), (-60, 47), (-65, 44), (-70, 42), (-74, 39), (-76, 35),
     (-80, 32), (-81, 26), (-84, 30), (-89, 21), (-90, 14), (-95, 16),
     (-97, 16), (-105, 20), (-110, 24), (-115, 29), (-120, 34), (-124, 40),
     (-124, 48), (-130, 55), (-140, 60), (-150, 61), (-158, 58), (-165, 60),
     (-168, 66)],
    # South America
    [(-80, 10), (-77, 7), (-75, 5), (-72, 2), (-70, 0), (-65, -3), (-60, -5),
     (-55, -2), (-50, 0), (-44, -3), (-38, -5), (-35, -8), (-38, -15),
     (-40, -20), (-45, -24), (-48, -28), (-52, -32), (-58, -35), (-62, -39),
     (-65, -43), (-68, -48), (-70, -52), (-72, -54), (-73, -45), (-73, -35),
     (-71, -25), (-72, -18), (-75, -15), (-78, -8), (-80, -3), (-80, 10)],
    # Africa
    [(-17, 15), (-15, 22), (-10, 30), (-6, 35), (0, 36), (10, 37), (12, 34),
     (20, 32), (25, 32), (30, 31), (32, 28), (35, 28), (38, 22), (40, 15),
     (43, 12), (48, 11), (51, 11), (51, 6), (48, 0), (42, -5), (40, -10),
     (38, -15), (35, -20), (33, -26), (30, -30), (28, -33), (20, -35),
     (18, -32), (15, -28), (13, -22), (12, -16), (10, -8), (9, -1), (9, 4),
     (4, 6), (-3, 5), (-8, 5), (-13, 8), (-17, 12), (-17, 15)],
    # Europe
    [(-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 47), (-4, 48), (-2, 50),
     (0, 50), (2, 51), (4, 53), (7, 54), (8, 57), (10, 58), (12, 56),
     (18, 56), (21, 55), (24, 58), (26, 60), (28, 61), (24, 64), (20, 66),
     (18, 69), (14, 67), (12, 65), (10, 63), (6, 62), (5, 60), (5, 58),
     (2, 57), (-2, 55), (-4, 53), (-5, 50), (-6, 47), (-8, 43), (-9, 39),
     (-10, 36)],
    # Asia
    [(30, 62), (35, 65), (40, 68), (50, 69), (60, 69), (68, 70), (75, 72),
     (85, 73), (95, 76), (105, 77), (115, 73), (125, 72), (135, 71),
     (145, 71), (155, 70), (165, 69), (170, 66), (178, 65), (175, 62),
     (170, 60), (162, 58), (158, 52), (150, 60), (145, 55), (142, 50),
     (140, 42), (138, 38), (135, 35), (130, 33), (127, 35), (124, 38),
     (122, 32), (120, 28), (117, 24), (112, 22), (108, 18), (105, 10),
     (103, 8), (100, 7), (98, 10), (96, 15), (93, 18), (90, 22), (88, 22),
     (85, 19), (80, 15), (77, 10), (75, 12), (73, 18), (70, 21), (67, 24),
     (62, 25), (58, 26), (55, 27), (52, 28), (50, 29), (48, 30), (45, 32),
     (42, 34), (39, 36), (36, 36), (33, 36), (30, 36), (28, 38), (27, 40),
     (28, 44), (28, 48), (28, 52), (28, 56), (28, 60), (30, 62)],
    # Australia
    [(114, -22), (114, -28), (115, -32), (118, -35), (124, -33), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -23), (146, -19), (142, -15), (142, -11), (137, -12), (132, -12),
     (130, -13), (126, -14), (122, -17), (118, -20), (114, -22)],
]

# (label, lon, lat) — red pins on the map
PINS = [
    ("RIYADH", 46.7, 24.6), ("GAZA", 34.5, 31.5), ("KYIV", 30.5, 50.5),
    ("BENGHAZI", 20.0, 32.1), ("KATHMANDU", 85.3, 27.7),
    ("JAKARTA", 106.8, -6.2), ("NEW YORK", -74.0, 40.7),
    ("LONDON", -0.1, 51.5), ("PARIS", 2.3, 48.9),
    ("STOCKHOLM", 18.1, 59.3), ("SANAA", 44.2, 15.4),
    ("KINSHASA", 25.0, -2.0), ("CARTAGENA", -75.5, 10.4),
]


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=MAP_BG)
    # graticule
    for k in range(1, 6):
        gx = x0 + (x1 - x0) * k / 6
        draw.line([(gx, y0), (gx, y1)], fill=MAP_LINE, width=1)
    for k in range(1, 4):
        gy = y0 + (y1 - y0) * k / 4
        draw.line([(x0, gy), (x1, gy)], fill=MAP_LINE, width=1)
    w, h = x1 - x0, y1 - y0

    def proj(lon, lat):
        # crop latitude to -55..75 so the strip is less squashed
        return (x0 + (lon + 180) / 360.0 * w,
                y0 + (75 - lat) / 130.0 * h)

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_LAND, outline=TEAL_DK)
    # pins
    for label, lon, lat in PINS:
        px, py = proj(lon, lat)
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=RED,
                     outline=(255, 255, 255), width=2)
    # caption bar inside the panel
    draw.rectangle([x0, y1 - 24, x1, y1], fill=TEAL_DK)
    draw.text((x0 + 10, y1 - 20),
              "THE DAY ON THE MAP  —  red pins mark the 13 places this page reports from",
              font=SANS_B(11), fill=(255, 255, 255))


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 26                      # side margin
    CW = W - 2 * MX              # content width

    # ---------------------------------------------------------- masthead
    y = 22
    d.text((MX, y), "THE WORLD TODAY", font=SERIF_B(56), fill=INK)
    tw = d.textlength("THE WORLD TODAY", font=SERIF_B(56))
    d.text((MX + tw + 14, y + 34), "EST. 2026", font=SANS_B(13), fill=GREY)
    y += 66
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=3)
    y += 8
    d.text((MX, y), "WEDNESDAY 25 NOVEMBER 2026",
           font=SANS_B(15), fill=RED)
    right = "39 STORIES  •  7 REGIONS  •  ONE DAY"
    d.text((MX + CW - d.textlength(right, font=SANS_B(15)), y), right,
           font=SANS_B(15), fill=INK)
    y += 24
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=1)

    # ---------------------------------------------------------- lead story
    y += 12
    d.text((MX, y), "MIDDLE EAST  —  WAR IN YEMEN", font=SANS_B(14),
           fill=RED)
    y += 22
    y = draw_wrapped(d, MX, y,
                     "Houthis hit Riyadh tower; Saudis strike back",
                     SERIF_B(34), CW, leading=40)
    y += 4
    y = draw_wrapped(
        d, MX, y,
        "A Houthi drone struck the PIF Tower in Riyadh for the second time in "
        "five days, injuring 11 — hours later Saudi jets hit Sanaa and "
        "Hodeidah port as the war spills across the Red Sea.",
        SERIF(16), CW, leading=21)
    y += 12

    # ---------------------------------------------------------- world map
    map_h = 165
    draw_map(d, (MX, y, MX + CW, y + map_h))
    y += map_h + 12

    # ---------------------------------------------------------- secondary leads
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=1)
    y += 10
    cols = [
        ("HUAWEI GUILTY ON 10 OF 12 COUNTS",
         "A Brooklyn jury convicted the Chinese telecom giant of stealing "
         "trade secrets and bank fraud — but cleared it of racketeering. "
         "Billions in fines loom; Huawei will appeal."),
        ("HUANG IS BACK — THEN SHARES SLIDE",
         "Nvidia's board unanimously reinstated Jensen Huang 11 days after "
         "he quit; the stock soared 31% on Monday, then fell 7% as he told "
         "staff he is in therapy."),
        ("UKRAINE'S WAR SPREADS TO LIBYA",
         "Zelenskyy confirmed Kyiv sank a Russian warship in Benghazi "
         "harbour and hit a cargo ship in the Gulf of Finland — as a leak "
         "put Russian war dead past 700,000."),
    ]
    col_w = (CW - 2 * 18) // 3
    top = y
    for i, (head, deck) in enumerate(cols):
        cx = MX + i * (col_w + 18)
        cy = top
        cy = draw_wrapped(d, cx, cy, head, SERIF_B(17), col_w, fill=RED,
                          leading=21)
        cy += 3
        cy = draw_wrapped(d, cx, cy, deck, SANS(12), col_w, leading=15)
        if i < 2:
            d.line([(cx + col_w + 9, top), (cx + col_w + 9, cy)],
                   fill=LIGHT, width=1)
    y = top + 108
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=1)
    y += 10

    # ---------------------------------------------------------- region grid
    regions = [
        ("AMERICAS", [
            ("CIA BREACH", "Hackers hit an unclassified CIA and ODNI intel system."),
            ("TURKEYS SPARED", "Trump pardons “Freedom” and “Feathers” at the 79th Thanksgiving rite."),
            ("FORT HOOD", "Shooter Hasan seeks a stay of execution due next week."),
            ("O'HARE HALTED", "Radar outage forces a second ground stop in two days."),
            ("IOWA BLAST", "Army to detonate five tons of lead azide today."),
            ("SCAM SWEEP", "Justice Dept charges 800+ in its largest-ever anti-fraud crackdown."),
            ("THANKSGIVING RUSH", "TSA expects 17.6m flyers; storm threatens parade balloons."),
            ("HOSTAGES", "Gunmen hold 25 people in a Cartagena supermarket."),
        ]),
        ("EUROPE", [
            ("SARKOZY TO TRIAL", "Ex-president and wife Carla Bruni face trial over Libya-funding claims."),
            ("SWEDEN STALEMATE", "Parliament votes 30 Nov on Kristersson as PM; 72 days without a government."),
            ("REAL 5–1 PSV", "Bellingham and Mbappé star as Madrid stay perfect in Europe."),
            ("ARSENAL HELD", "Dortmund peg back the Gunners 1–1; Cherki rescues City 2–2 vs Napoli."),
            ("COP31 COLLAPSE", "Antalya ends with no deal — the first COP without one since 2009."),
            ("EU SANCTIONS", "New package: visa ban for combatants in Russia's invasion."),
            ("HEAT TOLL", "England logged about 5,258 heat-linked deaths this summer."),
            ("SANTAS ASHORE", "Santa figures and a polar bear wash up on a Bulgarian beach."),
        ]),
        ("MIDDLE EAST & AFRICA", [
            ("GAZA STRIKE", "Israel kills Hamas security chief Naim Abu Nakhla; seven dead."),
            ("US WARNING", "Americans in the region told to stay vigilant amid Houthi threats."),
            ("BRITAIN SANCTIONS", "UK blacklists the Houthis and four leaders over Red Sea attacks."),
            ("ADEN UNDER FIRE", "Houthis shell al-Buraiqa district; 320,000 displaced since August."),
            ("IRAN CLAIM", "Israel alleges Tehran is developing chemical weapons."),
            ("GAZA TOLL", "1,679+ killed since the October ceasefire, Gaza authorities say."),
            ("EBOLA FLIGHT", "WHO evacuates staff from a hospital in Ituri, DR Congo, amid fighting."),
            ("DR CONGO", "Kinshasa sets a deadline on its local mining-control regulation."),
        ]),
        ("ASIA & OCEANIA", [
            ("NEPAL QUAKE", "M5.6 hits Taplejung near Tibet; tremors felt in India, Bhutan, Bangladesh."),
            ("MODI–MERZ", "Indian PM hosts the German chancellor to deepen the partnership."),
            ("SENSEX SLIDES", "Mumbai falls 1,484 points; the Nifty slips below 25,400."),
            ("JAKARTA", "MPR vets vice-presidential nominees Amran and Sugiono today."),
            ("$15BN DEAL", "Prabowo orders follow-up on a Chinese investment pact from Shenzhen."),
            ("BMKG ALERT", "Indonesia warned of extreme weather across regions through 26 Nov."),
            ("THAILAND", "Bangkok secures B800m in climate support after COP31."),
            ("SK HYNIX +20%", "Chip shares surge on Jensen Huang's return to Nvidia."),
        ]),
    ]
    col_w = (CW - 3 * 16) // 4
    top = y
    grid_bottom = top
    for i, (region, items) in enumerate(regions):
        cx = MX + i * (col_w + 16)
        cy = top
        d.text((cx, cy), region, font=SANS_B(13), fill=TEAL_DK)
        cy += 20
        d.line([(cx, cy), (cx + col_w, cy)], fill=TEAL, width=2)
        cy += 8
        for head, text in items:
            cy = draw_wrapped(d, cx, cy, head, SANS_B(12), col_w,
                              fill=INK, leading=14)
            cy = draw_wrapped(d, cx, cy, text, SANS(11), col_w, fill=(50, 48, 44),
                              leading=12)
            cy += 5
        grid_bottom = max(grid_bottom, cy)
    y = grid_bottom
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=1)

    # ---------------------------------------------------------- footer ticker
    y += 9
    y = draw_wrapped(
        d, MX, y,
        "MARKETS — Dell posts a record $54.94bn quarter  •  HP +14% as Walmsley "
        "named CEO  •  Sanofi buys Insmed for $41bn  •  Nasdaq −2%, Dow +400  •  "
        "Nikkei +3.9%, Seoul +6%  •  ALSO — Venezuela reports $237.5bn debt  •  "
        "New Zealand hold India to a draw in the 1st Test  •  Thomas Markle indicted",
        SANS_B(11), CW, fill=INK, leading=15)
    y += 6
    d.line([(MX, y), (MX + CW, y)], fill=INK, width=1)
    y += 5
    d.text((MX, y), "THE WORLD TODAY  •  Compiled from Reuters, AP, AFP, Xinhua, UEFA and national wires  •  All events of Wednesday 25 November 2026",
           font=SANS(9), fill=GREY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, "entry.png"), optimize=True)


if __name__ == "__main__":
    main()
