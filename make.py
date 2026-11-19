import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
BG = (14, 20, 36); PANEL = (28, 37, 60); TEXT = (236, 240, 248); MUTED = (140, 152, 178)
TEAL = (46, 196, 182); CORAL = (242, 98, 98); AMBER = (246, 182, 72); LINE = (60, 72, 100)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(size, w="SemiBold"):
    k = (size, w)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + f"Inter-{w}.otf", size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def P(t, a, b): return ease((t - a) / (b - a))
def mix(c1, c2, k): return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))
def fade(c, a): return mix(BG, c, clamp(a))
def lerp(a, b, k): return a + (b - a) * k

def text(d, xy, s, size, color=TEXT, a=1.0, w="SemiBold", anchor="la"):
    if a <= 0.01: return
    d.text(xy, s, font=font(size, w), fill=fade(color, a), anchor=anchor)

def wrap(s, size, maxw, w="Regular"):
    f = font(size, w); out, cur = [], ""
    for word in s.split():
        tst = (cur + " " + word).strip()
        if f.getlength(tst) <= maxw: cur = tst
        else: out.append(cur); cur = word
    if cur: out.append(cur)
    return out

def para(d, x, y, s, size, maxw, color=TEXT, a=1.0, w="Regular", lh=1.35):
    for i, ln in enumerate(wrap(s, size, maxw, w)):
        text(d, (x, y + i * size * lh), ln, size, color, a, w)
    return y + len(wrap(s, size, maxw, w)) * size * lh

def header(d, t, s):
    a = P(t, 0.1, 0.7)
    text(d, (70, 52 + (1 - a) * 12), s, 34, TEXT, a, "Bold")
    d.line([(70, 104), (70 + 90 * a, 104)], fill=fade(TEAL, a), width=4)

def caption(d, t, t0, s, color=MUTED, y=640, size=24):
    a = P(t, t0, t0 + 0.6)
    text(d, (W // 2, y + (1 - a) * 8), s, size, color, a, "Medium", "mm")

def phone(d, cx, cy, w=110, h=200, col=MUTED, a=1.0, fill=PANEL, width=4):
    if a <= 0.01: return
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=w * 0.16,
                        fill=fade(fill, a), outline=fade(col, a), width=width)
    d.rounded_rectangle([cx - w * 0.12, cy - h / 2 + h * 0.04, cx + w * 0.12, cy - h / 2 + h * 0.065],
                        radius=3, fill=fade(col, a * 0.7))

def lock(d, cx, cy, s, col, a=1.0, opened=0.0):
    if a <= 0.01: return
    c = fade(col, a); bw, bh = s, s * 0.8
    sy = cy - bh * 0.15 - opened * s * 0.35
    d.arc([cx - bw * 0.32, sy - bw * 0.62, cx + bw * 0.32, sy + bw * 0.02], 180, 360, fill=c, width=max(2, int(s * 0.13)))
    d.line([(cx - bw * 0.32, sy - bw * 0.3), (cx - bw * 0.32, cy - bh * 0.1)], fill=c, width=max(2, int(s * 0.13)))
    if opened < 0.5:
        d.line([(cx + bw * 0.32, sy - bw * 0.3), (cx + bw * 0.32, cy - bh * 0.1)], fill=c, width=max(2, int(s * 0.13)))
    d.rounded_rectangle([cx - bw / 2, cy - bh * 0.1, cx + bw / 2, cy + bh * 0.7], radius=s * 0.12, fill=c)
    d.ellipse([cx - s * 0.08, cy + bh * 0.2, cx + s * 0.08, cy + bh * 0.36], fill=fade(BG, 1))

def magnifier(d, cx, cy, r, col, a=1.0):
    if a <= 0.01: return
    c = fade(col, a)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=max(3, int(r * 0.18)))
    d.line([(cx + r * 0.7, cy + r * 0.7), (cx + r * 1.6, cy + r * 1.6)], fill=c, width=max(4, int(r * 0.3)))

def bubble(d, cx, cy, s, col, a=1.0, txtcol=BG, size=18, w="SemiBold"):
    if a <= 0.01: return
    f = font(size, w); tw = f.getlength(s)
    d.rounded_rectangle([cx - tw / 2 - 12, cy - size * 0.9, cx + tw / 2 + 12, cy + size * 0.9], radius=size * 0.6, fill=fade(col, a))
    text(d, (cx, cy), s, size, txtcol if a > 0.5 else fade(txtcol, a), 1, w, "mm")

def server(d, cx, cy, a=1.0, col=MUTED):
    for i in range(3):
        y = cy - 60 + i * 42
        d.rounded_rectangle([cx - 70, y, cx + 70, y + 34], radius=6, fill=fade(PANEL, a), outline=fade(col, a), width=3)
        d.ellipse([cx + 44, y + 13, cx + 52, y + 21], fill=fade(TEAL, a))

def arrow(d, x1, y1, x2, y2, col, a=1.0, width=4, dash=0):
    if a <= 0.01: return
    c = fade(col, a)
    if dash:
        L = math.hypot(x2 - x1, y2 - y1); n = int(L // dash)
        for i in range(0, n, 2):
            k1, k2 = i / n, min(1, (i + 1) / n)
            d.line([(lerp(x1, x2, k1), lerp(y1, y2, k1)), (lerp(x1, x2, k2), lerp(y1, y2, k2))], fill=c, width=width)
    else:
        d.line([(x1, y1), (x2, y2)], fill=c, width=width)
    ang = math.atan2(y2 - y1, x2 - x1); s = 14
    d.polygon([(x2, y2), (x2 - s * math.cos(ang - 0.45), y2 - s * math.sin(ang - 0.45)),
               (x2 - s * math.cos(ang + 0.45), y2 - s * math.sin(ang + 0.45))], fill=c)

def scales(d, cx, cy, s, col, a=1.0):
    c = fade(col, a); wd = max(3, int(s * 0.07))
    d.line([(cx, cy - s * 0.55), (cx, cy + s * 0.5)], fill=c, width=wd)
    d.line([(cx - s * 0.6, cy - s * 0.4), (cx + s * 0.6, cy - s * 0.4)], fill=c, width=wd)
    for sx in (-1, 1):
        px = cx + sx * s * 0.6
        d.line([(px, cy - s * 0.4), (px - s * 0.22, cy + s * 0.05)], fill=c, width=2)
        d.line([(px, cy - s * 0.4), (px + s * 0.22, cy + s * 0.05)], fill=c, width=2)
        d.chord([px - s * 0.26, cy - s * 0.1, px + s * 0.26, cy + s * 0.2], 0, 180, fill=c)
    d.rounded_rectangle([cx - s * 0.3, cy + s * 0.45, cx + s * 0.3, cy + s * 0.58], radius=3, fill=c)
    d.ellipse([cx - s * 0.08, cy - s * 0.64, cx + s * 0.08, cy - s * 0.48], fill=c)

# ---------------- scenes ----------------
def s_title(d, t):
    text(d, (W // 2, 210), "COMPUTER ETHICS  ·  GROUP PRESENTATION", 20, TEAL, P(t, 0.2, 0.9), "SemiBold", "mm")
    a = P(t, 0.6, 1.5)
    text(d, (W // 2, 300 + (1 - a) * 20), "Should our chats", 68, TEXT, a, "ExtraBold", "mm")
    text(d, (W // 2, 380 + (1 - a) * 20), "be scanned?", 68, TEXT, a, "ExtraBold", "mm")
    text(d, (W // 2, 470), "Client-side scanning of private messages: when, if ever, is it justified?", 24, MUTED, P(t, 1.6, 2.4), "Regular", "mm")
    text(d, (W // 2, 600), "Tommaso Ernst · Davide Bertoni · Fawaz Shahzad · Alessandro Callegari", 18, MUTED, P(t, 2.4, 3.0), "Medium", "mm")
    for i in range(3):
        lock(d, W // 2 - 40 + i * 40, 140, 22, [TEAL, AMBER, CORAL][i], P(t, 0.1 + i * 0.15, 0.6 + i * 0.15))

A_X, S_X, B_X, ROW = 210, 640, 1070, 370

def flow_base(d, t, scrambled_label=True):
    for x, lab in ((A_X, "Sender's phone"), (B_X, "Recipient's phone")):
        phone(d, x, ROW, a=P(t, 0.3, 0.9))
        text(d, (x, ROW + 125), lab, 20, MUTED, P(t, 0.5, 1.1), "Medium", "mm")
    server(d, S_X, ROW, P(t, 0.4, 1.0))
    text(d, (S_X, ROW + 125), "Provider's server", 20, MUTED, P(t, 0.6, 1.2), "Medium", "mm")
    d.line([(A_X + 70, ROW), (S_X - 85, ROW)], fill=fade(LINE, P(t, 0.6, 1.2)), width=3)
    d.line([(S_X + 85, ROW), (B_X - 70, ROW)], fill=fade(LINE, P(t, 0.6, 1.2)), width=3)

def packet(d, t, t_lock, t_go, t_arrive, msg):
    # message on A, locks, travels, unlocks at B
    if t < t_go:
        k = P(t, t_lock, t_lock + 0.6)
        if k < 0.5: bubble(d, A_X, ROW - 30, msg, TEXT, P(t, 1.0, 1.5), size=15)
        else: bubble(d, A_X, ROW - 30, "x7#k@9!q", MUTED, 1, BG, 15)
        lock(d, A_X, ROW + 40, 30, TEAL, P(t, t_lock, t_lock + 0.4), opened=1 - k)
    elif t < t_arrive:
        k = P(t, t_go, t_arrive)
        x = lerp(A_X, B_X, k); y = ROW - 30 - math.sin(k * math.pi) * 60
        bubble(d, x, y, "x7#k@9!q", MUTED, 1, BG, 15)
        lock(d, x, y + 34, 22, TEAL, 1)
    else:
        k = P(t, t_arrive + 0.3, t_arrive + 0.9)
        if k < 0.5: bubble(d, B_X, ROW - 30, "x7#k@9!q", MUTED, 1, BG, 15)
        else: bubble(d, B_X, ROW - 30, msg, TEXT, 1, size=15)
        lock(d, B_X, ROW + 40, 30, TEAL, 1, opened=k)

def s_e2ee(d, t):
    header(d, t, "1. How end-to-end encryption works")
    flow_base(d, t)
    packet(d, t, 2.0, 3.0, 5.6, "See you at 8!")
    a = P(t, 3.8, 4.4) * (1 - P(t, 5.6, 6.0))
    text(d, (S_X, ROW - 120), "sees only scrambled data", 20, AMBER, a, "SemiBold", "mm")
    caption(d, t, 6.6, "Only the sender and the recipient can read the message.", TEXT, size=26)

def s_css(d, t):
    header(d, t, "2. Client-side scanning")
    flow_base(d, t)
    # authorities box
    ab = P(t, 3.4, 4.0)
    d.rounded_rectangle([A_X - 95, 140, A_X + 95, 190], radius=10, fill=fade(PANEL, ab), outline=fade(CORAL, ab), width=3)
    text(d, (A_X, 165), "Authorities", 20, CORAL, ab, "Bold", "mm")
    # scan sweep on A
    if 1.6 <= t < 3.6:
        k = (t - 1.6) / 2.0
        mx = A_X - 30 + math.sin(k * math.pi * 2) * 30
        bubble(d, A_X, ROW - 30, "See you at 8!", TEXT, 1, size=15)
        magnifier(d, mx, ROW - 30, 24, CORAL, P(t, 1.6, 1.9) * (1 - P(t, 3.3, 3.6)))
        text(d, (A_X, ROW - 135), "CHECK BEFORE ENCRYPTING", 15, CORAL, P(t, 1.7, 2.1) * (1 - P(t, 3.1, 3.4)), "Bold", "mm")
        if t > 3.3: pass
    elif t < 1.6:
        bubble(d, A_X, ROW - 30, "See you at 8!", TEXT, P(t, 1.0, 1.5), size=15)
    if t >= 3.6 or t < 1.0:
        if t >= 3.6: packet(d, t, 3.6, 4.6, 7.0, "See you at 8!")
    arrow(d, A_X, ROW - 110, A_X, 200, CORAL, ab, 3, dash=10)
    text(d, (A_X + 14, ROW - 175), "report if match", 16, CORAL, ab, "Medium")
    caption(d, t, 7.6, "Encryption is not broken, it is bypassed:", TEXT, 610, 26)
    caption(d, t, 8.2, "the message is read before it is protected.", AMBER, 650, 26)

def s_eu(d, t):
    header(d, t, "3. The EU proposal: “Chat Control” (2022)")
    cols, rows = 8, 4
    for r in range(rows):
        for c in range(cols):
            cx, cy = 100 + c * 66, 190 + r * 105
            i = r * cols + c
            phone(d, cx, cy, 44, 80, MUTED, P(t, 0.3 + i * 0.01, 0.8 + i * 0.01), width=3)
            st = 1.4 + (c + r) * 0.12
            k = P(t, st, st + 0.4)
            if k > 0:
                pulse = 0.6 + 0.4 * math.sin((t - st) * 5)
                magnifier(d, cx - 4, cy - 4, 10, CORAL, k * pulse)
    text(d, (100 - 22, 620), "every user of the service", 18, CORAL, P(t, 3.0, 3.6), "SemiBold")
    bx = 690; items = [("Detection order", "covers a whole service, issued by a judicial or independent authority"),
                       ("AI classifiers", "search chats for known images, new images and grooming"),
                       ("On encrypted apps", "this means scanning on the phone before encryption")]
    y = 170
    for i, (h, s) in enumerate(items):
        a = P(t, 1.2 + i * 1.0, 1.8 + i * 1.0)
        d.ellipse([bx, y + 9, bx + 12, y + 21], fill=fade(CORAL, a))
        text(d, (bx + 26, y), h, 24, TEXT, a, "Bold")
        y = para(d, bx + 26, y + 34, s, 20, 500, MUTED, a) + 22
    a = P(t, 5.0, 5.6)
    d.rounded_rectangle([bx, 520, 1210, 600], radius=12, fill=fade(PANEL, a))
    text(d, (bx + 20, 535), "Status: still not law", 20, AMBER, a, "Bold")
    text(d, (bx + 20, 565), "5 negotiation rounds failed, the last on 29 June 2026", 18, MUTED, a, "Regular")

def s_tools(d, t):
    header(d, t, "4. These tools already exist")
    cards = [("Xinjiang, China", "2017 –", "The mandatory Jingwang app scans every file on the phone against a list of ‘dangerous’ files."),
             ("WeChat", "2020", "Images sent in chats are checked against a list of ‘sensitive’ files, even for accounts outside China."),
             ("North Korea", "today", "The keyboard rewrites words, and the phone takes a hidden screenshot every five minutes.")]
    for i, (h, yr, s) in enumerate(cards):
        a = P(t, 0.8 + i * 1.2, 1.5 + i * 1.2)
        x = 70 + i * 390; y = 160 + (1 - a) * 30
        d.rounded_rectangle([x, y, x + 360, y + 300], radius=16, fill=fade(PANEL, a), outline=fade(LINE, a), width=2)
        text(d, (x + 26, y + 28), yr, 18, CORAL, a, "Bold")
        text(d, (x + 26, y + 56), h, 28, TEXT, a, "Bold")
        para(d, x + 26, y + 110, s, 20, 310, MUTED, a)
    a = P(t, 4.8, 6.2)
    x1, x2 = 400, lerp(420, 880, a)
    if a > 0.02:
        d.line([(x1, 540), (x2, 540)], fill=fade(AMBER, a), width=6)
        d.polygon([(x2 + 18, 540), (x2, 528), (x2, 552)], fill=fade(AMBER, a))
    caption(d, t, 5.4, "Once these tools exist, their use tends to widen.", TEXT, 610, 28)

def s_panop(d, t):
    header(d, t, "5. Why scanning everyone is never justified")
    cx, cy, R = 330, 400, 200
    a = P(t, 0.3, 0.9)
    # beam
    ang = (t - 1.0) * 1.6
    if t > 1.0:
        k = P(t, 1.0, 1.6)
        pts = [(cx, cy)] + [(cx + math.cos(ang + da) * 250, cy + math.sin(ang + da) * 250) for da in (-0.28, 0.28)]
        d.polygon(pts, fill=fade((70, 62, 40), k))
    # tower
    d.rectangle([cx - 22, cy - 60, cx + 22, cy + 40], fill=fade(PANEL, a), outline=fade(AMBER, a), width=3)
    d.polygon([(cx - 34, cy - 60), (cx + 34, cy - 60), (cx, cy - 95)], fill=fade(AMBER, a))
    shrink = P(t, 2.5, 6.0)
    for i in range(14):
        th = i / 14 * math.tau
        px, py = cx + math.cos(th) * R, cy + math.sin(th) * R * 0.85
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=fade(TEXT, a))
        bw = lerp(46, 10, shrink); bh = lerp(22, 8, shrink)
        ba = a * lerp(1, 0.5, shrink)
        d.rounded_rectangle([px - bw / 2, py - 24 - bh, px + bw / 2, py - 20], radius=6, fill=fade(TEAL, ba))
    tx = 640
    a1 = P(t, 1.2, 1.8)
    text(d, (tx, 170), "Privacy is a social good", 28, TEXT, a1, "Bold")
    para(d, tx, 214, "Tied to autonomy, democracy and freedom, not just one person’s interest (Regan).", 21, 560, MUTED, a1)
    a2 = P(t, 3.0, 3.6)
    text(d, (tx, 330), "The Panopticon", 28, TEXT, a2, "Bold")
    para(d, tx, 374, "People only need to believe their chats are read to change how they talk.", 21, 560, MUTED, a2)
    a3 = P(t, 5.2, 5.8)
    text(d, (tx, 490), "Scanning everyone → self-censorship and fear", 22, AMBER, a3, "SemiBold")

def s_ladder(d, t):
    header(d, t, "6. Why a suspect is different")
    left = ["Their private chats", "Public safety", "Public data"]
    colsx = [150, 690]
    titles = ["Everyone (the default)", "A person with concrete evidence"]
    for j in range(2):
        a = P(t, 0.4 + j * 0.6, 1.0 + j * 0.6)
        text(d, (colsx[j], 160), titles[j], 26, AMBER if j else TEAL, a, "Bold")
        text(d, (colsx[j], 196), "top = highest value", 16, MUTED, a, "Medium")
    sw = P(t, 3.0, 4.6)
    for j in range(2):
        a = P(t, 0.6 + j * 0.6, 1.2 + j * 0.6)
        for i, s in enumerate(left):
            slot = i
            if j == 1 and i in (0, 1):
                slot = lerp(i, 1 - i, sw)
            y = 250 + slot * 90
            off = 0
            if j == 1 and i in (0, 1): off = math.sin(sw * math.pi) * (70 if i == 0 else -70)
            x = colsx[j] + off
            hl = (j == 1 and i == 1 and sw > 0.5) or (j == 0 and i == 0)
            col = (AMBER if j else TEAL) if hl else LINE
            d.rounded_rectangle([x, y, x + 440, y + 68], radius=12, fill=fade(PANEL, a), outline=fade(col, a), width=3)
            rank = int(round(slot)) + 1
            text(d, (x + 26, y + 34), str(rank), 26, MUTED, a, "Bold", "lm")
            text(d, (x + 70, y + 34), s, 24, TEXT, a, "SemiBold", "lm")
    caption(d, t, 5.2, "The order flips for one person, and only on concrete evidence.", TEXT, 580, 26)
    caption(d, t, 6.0, "Never for everyone. Profiling from aggregated data is not evidence.", MUTED, 625, 22)

def s_model(d, t):
    header(d, t, "7. Our model: targeted and judge-approved")
    cols, rows = 6, 3; SUS = (1, 3)
    for r in range(rows):
        for c in range(cols):
            cx, cy = 100 + c * 78, 210 + r * 135
            i = r * cols + c
            sus = (r, c) == SUS
            hk = P(t, 2.6, 3.2) if sus else 0
            phone(d, cx, cy, 52, 96, mix(MUTED, AMBER, hk), P(t, 0.3 + i * 0.02, 0.8 + i * 0.02), width=3 + int(hk * 2))
            if not sus or t < 6.2:
                lock(d, cx, cy + 4, 20, TEAL, P(t, 1.0 + i * 0.03, 1.4 + i * 0.03))
            if sus and t >= 6.2:
                magnifier(d, cx - 3, cy - 3, 13, AMBER, P(t, 6.2, 6.6))
    text(d, (78, 615), "E2EE for everyone, nobody scanned by default", 17, TEAL, P(t, 1.4, 2.0), "SemiBold")
    sx, sy = 100 + 3 * 78, 210 + 135
    # judge
    jx, jy = 330, 128
    ja = P(t, 4.0, 4.6)
    if ja > 0:
        d.rounded_rectangle([jx - 150, jy - 22, jx + 150, jy + 22], radius=10, fill=fade(PANEL, ja), outline=fade(AMBER, ja), width=2)
        scales(d, jx - 120, jy, 26, AMBER, ja)
        text(d, (jx - 92, jy), "Judge: approved, 30 days", 17, AMBER, ja, "Bold", "lm")
        arrow(d, jx + 60, jy + 24, sx + 10, sy - 56, AMBER, P(t, 4.6, 5.2), 3, dash=9)
    # timer bar under suspect
    if t > 6.4:
        k = clamp((t - 6.4) / 6.0)
        d.rounded_rectangle([sx - 30, sy + 56, sx + 30, sy + 62], radius=3, fill=fade(LINE, 1))
        d.rounded_rectangle([sx - 30, sy + 56, sx - 30 + 60 * (1 - k), sy + 62], radius=3, fill=fade(AMBER, 1))
    steps = [("E2EE for everyone", "No one's chats are scanned by default."),
             ("Concrete evidence", "Evidence or reports, never profiling."),
             ("Impartial judge", "Approves each case, for a limited time."),
             ("Targeted scanning", "Only the suspect, only content named in the order."),
             ("Redress", "Human review, audit, right to appeal.")]
    tx = 640
    times = [1.2, 2.8, 4.2, 6.2, 8.0]
    for i, (h, s) in enumerate(steps):
        a = P(t, times[i], times[i] + 0.6); y = 150 + i * 92
        d.ellipse([tx, y, tx + 40, y + 40], fill=fade(AMBER if i else TEAL, a))
        text(d, (tx + 20, y + 20), str(i + 1), 20, BG if a > 0.5 else fade(BG, a), 1, "Bold", "mm")
        text(d, (tx + 58, y - 2), h, 24, TEXT, a, "Bold")
        text(d, (tx + 58, y + 30), s, 19, MUTED, a, "Regular")
    caption(d, t, 9.6, "Rules, criteria and number of cases are public.", TEXT, 655, 22)

def s_end(d, t):
    a = P(t, 0.3, 1.1)
    text(d, (W // 2, 290 + (1 - a) * 16), "Never for everyone.", 64, TEXT, a, "ExtraBold", "mm")
    b = P(t, 1.4, 2.2)
    text(d, (W // 2, 380 + (1 - b) * 16), "Only for a suspect, under a judge.", 48, AMBER, b, "Bold", "mm")
    c = P(t, 2.8, 3.5)
    text(d, (W // 2, 480), "End-to-end encryption must stay protected for everyone.", 24, MUTED, c, "Regular", "mm")
    lock(d, W // 2, 175, 44, TEAL, P(t, 0.1, 0.6))

SCENES = [("01_title", s_title, 6), ("02_e2ee", s_e2ee, 9), ("03_css", s_css, 11), ("04_eu", s_eu, 10),
          ("05_tools", s_tools, 9), ("06_panop", s_panop, 9), ("07_ladder", s_ladder, 9),
          ("08_model", s_model, 13), ("09_end", s_end, 7)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    fn(d, t)
    f = min(clamp(t / 0.4), clamp((dur - t) / 0.4))
    if f < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, f)
    return im

if __name__ == "__main__":
    out = sys.argv[1]; mode = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    if mode == "stills":
        for name, fn, dur in SCENES:
            frame(fn, dur - 0.6, dur).save(f"{out}/{name}.png")
        frame(s_css, 2.5, 11).save(f"{out}/03b.png"); frame(s_e2ee, 4.5, 9).save(f"{out}/02b.png")
        frame(s_ladder, 3.8, 9).save(f"{out}/07b.png")
    else:
        for name, fn, dur in SCENES:
            tmp = f"{out}/{name}.tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                  "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                                  "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for i in range(int(dur * FPS)):
                p.stdin.write(frame(fn, i / FPS, dur).tobytes())
            p.stdin.close()
            if p.wait() == 0: os.rename(tmp, f"{out}/{name}.mp4")
            print(name, "done", flush=True)
