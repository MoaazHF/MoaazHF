#!/usr/bin/env python3
"""Generates assets/notebook.svg and checks it against README.md.

Needs: pip install fonttools brotli
Run:   python scripts/build.py
"""
import base64
import io
import math
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "notebook.svg"
MAX_BYTES = 200_000

W, LEFT, RIGHT, MARGIN = 880, 56, 824, 560

FONTS = {
    "sans": ("InstrumentSans.ttf", {"wdth": 100, "wght": (400, 600)}),
    "serif": ("Newsreader.ttf", {"opsz": 14, "wght": 420}),
}
loaded = {
    name: instancer.instantiateVariableFont(TTFont(ROOT / "scripts" / "fonts" / file), axes)
    for name, (file, axes) in FONTS.items()
}
used = {name: set() for name in FONTS}
body = []

# class -> (font, css). The sans is the work, the serif is the voice in the margin.
STYLES = {
    "title": ("sans", "font-size:80px;font-weight:500;letter-spacing:-.036em;fill:var(--ink)"),
    "h2": ("sans", "font-size:36px;font-weight:500;letter-spacing:-.028em;fill:var(--ink)"),
    "h3": ("sans", "font-size:25px;font-weight:550;letter-spacing:-.015em;fill:var(--ink)"),
    "note": ("sans", "font-size:22px;letter-spacing:-.004em;fill:var(--ink)"),
    "sub": ("sans", "font-size:20px;letter-spacing:-.004em;fill:var(--graphite)"),
    "cap": ("sans", "font-size:18px;fill:var(--faint)"),
    "pill": ("sans", "font-size:18px;fill:var(--graphite)"),
    "voice": ("serif", "font-size:22.5px;letter-spacing:.004em;fill:var(--ink)"),
    "label": ("serif", "font-size:26px;letter-spacing:.004em;fill:var(--ink)"),
    "mark": ("serif", "font-size:30px;letter-spacing:-.01em;fill:var(--ink)"),
    "big": ("serif", "font-size:37px;letter-spacing:-.006em;fill:var(--ink)"),
}


def measure(s, cls):
    """Text width in px, from font advances. Ignores kerning, close enough for pills."""
    font_name, css = STYLES[cls]
    font = loaded[font_name]
    size = float(re.search(r"font-size:([\d.]+)", css).group(1))
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in s) * size / font["head"].unitsPerEm


def text(x, y, s, cls, anchor=None):
    used[STYLES[cls][0]].update(s)
    attrs = f' text-anchor="{anchor}"' if anchor else ""
    body.append(f'<text x="{x}" y="{y}" class="{cls}"{attrs}>{escape(s)}</text>')


def lines(x, y, rows, cls, step):
    for i, row in enumerate(rows):
        text(x, y + i * step, row, cls)
    return y + len(rows) * step


def pencil(d, delay=0, dur=0.9):
    body.append(
        f'<path class="pencil" pathLength="1" d="{d}" '
        f'style="animation:draw {dur}s cubic-bezier(.4,.1,.5,1) {delay}s both"/>'
    )


def wobble(x1, y1, x2, y2, seed, amp=1.6):
    """Hand-drawn line: midpoint-smoothed quadratics through jittered points."""
    rng = random.Random(seed)
    n = max(3, int(abs(x2 - x1) / 44))
    pts = [
        (x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n + (rng.uniform(-amp, amp) if 0 < i < n else 0))
        for i in range(n + 1)
    ]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for a, b in zip(pts[1:], pts[2:]):
        d += f" Q{a[0]:.1f} {a[1]:.1f} {(a[0] + b[0]) / 2:.1f} {(a[1] + b[1]) / 2:.1f}"
    return d + f" L{pts[-1][0]:.1f} {pts[-1][1]:.1f}"


def blot(cx, cy, r, seed, delay=None):
    """Generated ink blot: an irregular closed blob plus a few stray drops."""
    rng = random.Random(seed)
    n, pts = 14, []
    for i in range(n):
        angle = math.tau * i / n
        radius = r * (1 + rng.uniform(-0.2, 0.2))
        pts.append((radius * math.cos(angle), radius * math.sin(angle)))
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    start = mid(pts[-1], pts[0])
    d = f"M{start[0]:.2f} {start[1]:.2f}"
    for i, p in enumerate(pts):
        m = mid(p, pts[(i + 1) % n])
        d += f" Q{p[0]:.2f} {p[1]:.2f} {m[0]:.2f} {m[1]:.2f}"
    drops = ""
    for _ in range(3):
        angle, dist = rng.uniform(0, math.tau), r * rng.uniform(1.35, 1.8)
        drops += (
            f'<circle cx="{dist * math.cos(angle):.2f}" cy="{dist * math.sin(angle):.2f}" '
            f'r="{r * rng.uniform(.07, .16):.2f}"/>'
        )
    anim = f' style="animation:splat .46s cubic-bezier(.2,.9,.25,1.12) {delay}s both"' if delay is not None else ""
    body.append(
        f'<g transform="translate({cx} {cy})"><g class="blot" filter="url(#edge)"{anim}>'
        f'<path d="{d} Z"/>{drops}</g></g>'
    )


def margin_note(y, rows, seed, delay=None):
    for row in rows:
        assert MARGIN + measure(row, "voice") <= W - 32, f"margin note too wide: {row}"
    blot(MARGIN - 16, y - 7, 4.5, seed, delay)
    lines(MARGIN, y, rows, "voice", 30)


def pills(x, y, items):
    """Wraps pills to the right edge and returns the y of the row below."""
    for item in items:
        width = measure(item, "pill") + 30
        if x + width > RIGHT:
            x, y = 236, y + 46
        body.append(
            f'<rect class="ring" x="{x:.1f}" y="{y - 24}" width="{width:.1f}" height="36" rx="18"/>'
        )
        text(round(x + width / 2, 1), y, item, "pill", anchor="middle")
        x += width + 8
    return y + 46


# --- Hero ---------------------------------------------------------------------
blot(68, 56, 8.5, 7, delay=0)
text(90, 66, "moaaz.", "mark")
text(RIGHT, 64, "Cairo, Egypt", "cap", anchor="end")

text(LEFT - 3, 186, "Moaaz Hassan.", "title")

y = 262
INTRO = [
    "Full-Stack Developer and Computer Science",
    "student focused on backend services, API",
    "design, and web platforms using NestJS,",
    "React, TypeScript, PostgreSQL, and Docker.",
]
lines(LEFT, y, INTRO, "note", 36)
underline_end = LEFT + measure(INTRO[1], "note")
pencil(wobble(LEFT, y + 44, underline_end, y + 44, 3), delay=0.6, dur=1.0)
pencil(
    f"M{underline_end + 4:.0f} {y + 42} C{underline_end + 30:.0f} {y + 40} {MARGIN - 44} {y + 24} {MARGIN - 24} {y - 2}",
    delay=1.5, dur=0.5,
)
margin_note(
    y + 4,
    ["Currently contributing to", "a Saudi food delivery", "platform across ordering,",
     "logistics, payments,", "dashboards, and", "operational workflows."],
    11,
    delay=1.8,
)

# --- Experience ---------------------------------------------------------------
y = 498
text(LEFT, y, "Experience", "h2")
y += 62
text(LEFT, y, "Full-Stack Developer", "h3")
text(LEFT, y + 36, "RobinFood (BAHJA AL-TAUM For IT LLC)", "note")
text(LEFT, y + 68, "Saudi Arabia / Mar 2026 – Present", "cap")
pencil(wobble(LEFT, y + 46, 460, y + 46, 5), delay=2.6)
margin_note(y + 4, ["Still shipping."], 13)

# --- Projects -----------------------------------------------------------------
y += 146
text(LEFT, y, "Projects", "h2")
y += 62
PROJECTS = [
    ("Tourism Agency Platform", "React / Vite / TailwindCSS / Framer Motion"),
    ("Task Management System", "NestJS / TypeORM / PostgreSQL / Ionic React"),
    ("Wassalha P2P Logistics", "React / React Router / TailwindCSS"),
    ("Subscription Box Platform", "Laravel / PHP / PostgreSQL / TailwindCSS"),
]
STEP = 136
rows = [y + i * STEP for i in range(4)]
for row, (name, stack) in zip(rows, PROJECTS):
    text(LEFT, row, name, "h3")
    text(LEFT, row + 34, stack, "sub")
margin_note(rows[0] + 4, ["A real client, live on", "Vercel. Built in a", "2-week sprint."], 17)
margin_note(rows[2] + 4, ["CS systems-analysis", "coursework."], 19)
margin_note(rows[3] + 4, ["Software engineering", "coursework, as a team."], 23)

# The thread: out to a remark, back under the note, round to the next project.
dot = MARGIN - 22
a, b, c, d = rows
pencil(
    f"M{LEFT + measure(PROJECTS[0][0], 'h3') + 8:.0f} {a - 8} C400 {a - 16} 500 {a - 18} {dot} {a - 4}",
    delay=2.8, dur=0.5,
)
pencil(
    f"M{dot} {a + 8} C{dot - 30} {a + 72} 340 {a + 76} 150 {a + 72} "
    f"C60 {a + 70} 18 {b - 30} 26 {b - 14} C30 {b - 6} 38 {b - 4} {LEFT - 8} {b - 6}",
    delay=3.2, dur=1.1,
)
pencil(
    f"M26 {b + 2} C22 {b + 50} 60 {b + 72} 170 {b + 74} "
    f"C340 {b + 78} {dot - 40} {b + 76} {dot} {c - 4}",
    delay=4.2, dur=1.0,
)
pencil(
    f"M{dot} {c + 8} C{dot - 30} {c + 72} 340 {c + 76} 150 {c + 72} "
    f"C60 {c + 70} 18 {d - 30} 26 {d - 14} C30 {d - 6} 38 {d - 4} {LEFT - 8} {d - 6}",
    delay=5.1, dur=1.1,
)
pencil(
    f"M{LEFT + measure(PROJECTS[3][0], 'h3') + 8:.0f} {d - 8} C400 {d - 16} 500 {d - 18} {dot} {d - 4}",
    delay=6.1, dur=0.5,
)

# --- Training -----------------------------------------------------------------
y = d + 118
text(LEFT, y, "Training & Courses", "h2")
y += 56
TRAINING = [
    (LEFT, "ITI", "Web Development .NET", "120h / Jul 2025"),
    (316, "DEPI", "React Development", "159h / Jul 2026"),
    (576, "NTI AWS Academy", "Cloud Foundations + SAA", "90h / Sep 2026"),
]
for i, (x, label, course, meta) in enumerate(TRAINING):
    blot(x + 7, y, 6, 29 + i, delay=6.6 + i * 0.7)
    if i < 2:
        next_x = TRAINING[i + 1][0]
        pencil(wobble(x + 24, y, next_x - 16, y, 31 + i, amp=2.4), delay=6.8 + i * 0.7, dur=0.5)
        pencil(f"M{next_x - 26} {y - 7} L{next_x - 16} {y} L{next_x - 26} {y + 7}", delay=7.2 + i * 0.7, dur=0.2)
    text(x, y + 44, label, "label")
    text(x, y + 78, course, "sub")
    text(x, y + 108, meta, "cap")
y += 166
blot(LEFT + 6, y - 7, 4.5, 37)
text(LEFT + 24, y, "Also self-studying Backend from First Principles (YouTube).", "voice")

# --- Skills -------------------------------------------------------------------
y += 92
text(LEFT, y, "Skills & Abilities", "h2")
y += 56
SKILLS = [
    ("Languages", ["TypeScript", "JavaScript ES6+", "SQL", "C"]),
    ("Frontend", ["React.js", "Ionic React", "TailwindCSS", "Ant Design", "Vite", "Framer Motion"]),
    ("Backend", ["Node.js", "NestJS", "Express.js", "REST & GraphQL", "TypeORM"]),
    ("Data & Messaging", ["PostgreSQL", "Redis", "RabbitMQ", "BullMQ"]),
    ("Tooling", ["Docker & Compose", "Git & GitHub", "Vercel", "Postman"]),
    ("Practices", ["Data Structures & Algorithms", "OOP & SOLID", "Software Testing", "Agile"]),
    ("Working Style", ["Problem-Solving", "Root-Cause Analysis", "System Design Trade-offs", "Communication", "Teamwork"]),
]
for category, items in SKILLS:
    text(LEFT, y, category, "cap")
    y = pills(236, y, items) + 10

# --- Education ----------------------------------------------------------------
y += 58
text(LEFT, y, "Education", "h2")
y += 62
text(LEFT, y, "B.Sc. Computer Science", "h3")
text(LEFT, y + 36, "Capital University (Helwan)", "note")
text(LEFT, y + 68, "Cairo, Egypt / Expected Graduation: 2028", "cap")
margin_note(y + 4, ["In progress."], 41)

# --- Sign-off -----------------------------------------------------------------
y += 164
pencil(wobble(LEFT, y - 58, RIGHT, y - 58, 43, amp=1.2), delay=7)
text(LEFT, y, "Open to backend & full-stack opportunities.", "big")
y += 44
text(LEFT, y, "English: professional reading, writing & speaking.", "sub")
blot(RIGHT - 8, y - 8, 7, 47)
HEIGHT = y + 66


def font_face(name):
    source = TTFont(ROOT / "scripts" / "fonts" / FONTS[name][0], recalcTimestamp=False)
    source = instancer.instantiateVariableFont(source, FONTS[name][1])
    options = subset.Options(layout_features=["kern", "liga"], notdef_outline=True)
    subsetter = subset.Subsetter(options)
    subsetter.populate(text="".join(sorted(used[name])) + " ")
    subsetter.subset(source)
    source.flavor = "woff2"
    out = io.BytesIO()
    source.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    weight = "400 600" if name == "sans" else "400"
    return f"@font-face{{font-family:nb-{name};font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}"


css = "".join(
    f".{cls}{{font-family:nb-{font},{'ui-sans-serif,system-ui,sans-serif' if font == 'sans' else 'ui-serif,Georgia,serif'};{rule}}}"
    for cls, (font, rule) in STYLES.items()
)

# Paper matches GitHub's page colours (light and default dark).
# Text never animates, so a renderer that freezes on the first frame loses only
# decoration. Keyframes define just the start state, so the resting frame is complete.
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{HEIGHT}" viewBox="0 0 {W} {HEIGHT}" role="img" aria-label="Moaaz Hassan, Full-Stack Developer. Full text follows the image.">
<style>
{font_face("sans")}
{font_face("serif")}
:root{{--paper:#ffffff;--ink:#1d1c1a;--graphite:#5c5953;--faint:#8e8a83;--rule:#dedbd4}}
@media (prefers-color-scheme:dark){{:root{{--paper:#0d1117;--ink:#e9e7e2;--graphite:#a9a69e;--faint:#7a776f;--rule:#33322f}}}}
.paper{{fill:var(--paper)}}
.blot{{fill:var(--ink);transform-box:fill-box;transform-origin:center}}
.ring{{fill:none;stroke:var(--rule);stroke-width:1.2}}
.pencil{{fill:none;stroke:var(--graphite);stroke-opacity:.6;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:0}}
{css}
@keyframes draw{{from{{stroke-dashoffset:1}}}}
@keyframes splat{{from{{transform:scale(.12);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<filter id="edge" x="-40%" y="-40%" width="180%" height="180%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="2"/></filter>
<clipPath id="sheet"><rect width="{W}" height="{HEIGHT}" rx="14"/></clipPath>
</defs>
<g clip-path="url(#sheet)">
<rect class="paper" width="{W}" height="{HEIGHT}"/>
{chr(10).join(body)}
</g>
</svg>
"""
OUT.write_text(svg, encoding="utf-8")

# --- Checks -------------------------------------------------------------------
ET.fromstring(svg)
size = OUT.stat().st_size
assert size <= MAX_BYTES, f"{size} bytes is over the {MAX_BYTES} budget"
external = set(re.findall(r"https?://[^\"')\s]+", svg)) - {"http://www.w3.org/2000/svg"}
assert not external, f"external URLs: {external}"

FACTS = [
    "Moaaz Hassan", "Cairo, Egypt", "Full-Stack Developer", "Computer Science",
    "NestJS", "TypeScript", "PostgreSQL", "Docker", "Saudi food delivery",
    "RobinFood", "BAHJA AL-TAUM For IT LLC", "Saudi Arabia", "Mar 2026 – Present",
    "Tourism Agency Platform", "Task Management System", "Wassalha P2P Logistics",
    "Subscription Box Platform", "Vercel", "2-week sprint", "Laravel", "Ionic React",
    "Web Development .NET", "120h", "Jul 2025", "React Development", "159h", "Jul 2026",
    "NTI AWS Academy", "Cloud Foundations + SAA", "90h", "Sep 2026",
    "Backend from First Principles", "Capital University (Helwan)", "B.Sc. Computer Science",
    "Expected Graduation: 2028", "backend & full-stack opportunities",
    "professional reading, writing & speaking",
] + [skill for _, items in SKILLS for skill in items] + [category for category, _ in SKILLS]

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for fact in FACTS:
    assert escape(fact) in svg, f"missing from SVG: {fact}"
    assert fact in readme, f"missing from README: {fact}"
for contact in ["moazhasanfarouk@gmail.com", "github.com/MoaazHF", "linkedin.com/in/moazhasan"]:
    assert contact in readme, f"missing from README: {contact}"
assert "assets/notebook.svg" in readme

print(f"{OUT.relative_to(ROOT)}: {size / 1000:.0f} KB, {W}x{HEIGHT}")
