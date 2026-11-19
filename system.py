import math, random, subprocess, sys, os
from PIL import Image, ImageDraw
from make import (W, H, FPS, BG, PANEL, TEXT, MUTED, TEAL, CORAL, AMBER, LINE, font, clamp, ease, P, mix, fade,
                  lerp, text, phone, lock, magnifier, bubble, server, arrow, scales)

GREEN = (92, 206, 120)
XS, YS = [110, 240, 370], [215, 375, 535]
USERS = [(x, y) for y in YS for x in XS]
SUS = 4
SRV = (640, 375)
ACT = {"police": (920, 215), "judge": (1140, 215), "review": (920, 535), "audit": (1140, 535)}
LABEL = {"police": "Police", "judge": "Judge", "review": "Human reviewer", "audit": "Audit & public report"}

# ---------- icons ----------
def shield(d, cx, cy, s, col, a):
    c = fade(col, a)
    d.polygon([(cx - s * .5, cy - s * .5), (cx + s * .5, cy - s * .5), (cx + s * .5, cy), (cx, cy + s * .6), (cx - s * .5, cy)], fill=c)
    d.polygon([(cx - s * .3, cy - s * .32), (cx + s * .3, cy - s * .32), (cx + s * .3, cy - .02 * s), (cx, cy + s * .34), (cx - s * .3, cy - .02 * s)], fill=fade(PANEL, a))

def person(d, cx, cy, s, col, a):
    c = fade(col, a)
    d.ellipse([cx - s * .22, cy - s * .55, cx + s * .22, cy - s * .11], fill=c)
    d.chord([cx - s * .45, cy - s * .02, cx + s * .45, cy + s * .8], 180, 360, fill=c)

def document(d, cx, cy, s, col, a, lines=3):
    c = fade(col, a)
    d.rounded_rectangle([cx - s * .38, cy - s * .5, cx + s * .38, cy + s * .5], radius=4, outline=c, width=3, fill=fade(PANEL, a))
    for i in range(lines):
        y = cy - s * .28 + i * s * .2
        d.line([(cx - s * .22, y), (cx + s * (.22 if i < lines - 1 else .05), y)], fill=c, width=3)

def check(d, cx, cy, s, col, a, k=1.0):
    if a <= 0.01: return
    c = fade(col, a); p1, p2, p3 = (cx - s * .5, cy), (cx - s * .15, cy + s * .35), (cx + s * .5, cy - s * .4)
    if k < 0.4:
        q = k / 0.4; d.line([p1, (lerp(p1[0], p2[0], q), lerp(p1[1], p2[1], q))], fill=c, width=max(3, int(s * .18)))
    else:
        q = (k - .4) / .6
        d.line([p1, p2, (lerp(p2[0], p3[0], q), lerp(p2[1], p3[1], q))], fill=c, width=max(3, int(s * .18)), joint="curve")

def cross(d, cx, cy, s, col, a):
    c = fade(col, a); w = max(3, int(s * .18))
    d.line([(cx - s / 2, cy - s / 2), (cx + s / 2, cy + s / 2)], fill=c, width=w)
    d.line([(cx - s / 2, cy + s / 2), (cx + s / 2, cy - s / 2)], fill=c, width=w)

def chip(d, x, y, a=1.0):
    d.rounded_rectangle([x - 24, y - 12, x + 24, y + 12], radius=8, fill=fade(MUTED, a))
    text(d, (x, y), "#x7@k", 11, BG, 1 if a > .5 else 0, "Bold", "mm")
    lock(d, x + 30, y - 4, 12, TEAL, a)

def plain_msg(d, x, y, a=1.0, col=TEXT):
    if a <= .01: return
    d.rounded_rectangle([x - 26, y - 14, x + 26, y + 14], radius=8, fill=fade(col, a))
    d.line([(x - 16, y - 4), (x + 16, y - 4)], fill=fade(MUTED, a), width=3)
    d.line([(x - 16, y + 5), (x + 6, y + 5)], fill=fade(MUTED, a), width=3)

def match_item(d, x, y, a=1.0):
    if a <= .01: return
    d.rounded_rectangle([x - 22, y - 18, x + 22, y + 18], radius=6, fill=fade(PANEL, a), outline=fade(CORAL, a), width=3)
    d.polygon([(x - 14, y + 11), (x - 3, y - 4), (x + 5, y + 5), (x + 9, y), (x + 15, y + 11)], fill=fade(CORAL, a))
    d.ellipse([x + 4, y - 12, x + 11, y - 5], fill=fade(CORAL, a))

# ---------- world ----------
def actors(d, act, base=1.0):
    for k, (cx, cy) in ACT.items():
        lv = act.get(k, 0.0)
        a = base * lerp(0.32, 1.0, lv)
        col = mix(LINE, {"police": (110, 150, 245), "judge": AMBER, "review": TEAL, "audit": MUTED}[k], lv)
        d.rounded_rectangle([cx - 88, cy - 62, cx + 88, cy + 62], radius=14, fill=fade(PANEL, a), outline=fade(col, a), width=3)
        ic = mix(MUTED, col, lv)
        if k == "police": shield(d, cx, cy - 16, 42, ic, a)
        if k == "judge": scales(d, cx, cy - 16, 40, ic, a)
        if k == "review": person(d, cx - 8, cy - 14, 40, ic, a); magnifier(d, cx + 16, cy - 14, 9, ic, a)
        if k == "audit": document(d, cx, cy - 16, 44, ic, a)
        text(d, (cx, cy + 40), LABEL[k], 17, TEXT, a, "SemiBold", "mm")

def users(d, ua=1.0, sus=0.0, scan=0.0, locks=1.0, stagger_t=None, slabel=1.0):
    for i, (x, y) in enumerate(USERS):
        a = ua if stagger_t is None else P(stagger_t, i * .08, i * .08 + .5)
        s = sus if i == SUS else 0
        phone(d, x, y, 62, 104, mix(MUTED, AMBER, s), a, width=3 + int(s * 2))
        if i == SUS and scan > 0:
            lock(d, x, y + 4, 22, TEAL, a * locks * (1 - scan))
            magnifier(d, x - 3, y - 3, 14, AMBER, a * scan)
        else:
            lock(d, x, y + 4, 22, TEAL, a * locks)
    if sus > 0:
        x, y = USERS[SUS]
        text(d, (x, y - 68), "SUSPECT", 14, AMBER, sus * slabel, "Bold", "mm")

def world_server(d, a=1.0, label=1.0):
    server(d, SRV[0], SRV[1], a)
    text(d, (SRV[0], SRV[1] + 95), "Chat provider", 18, MUTED, a * label, "Medium", "mm")

def via(A, B, k):
    if k < .5:
        q = k / .5; return lerp(A[0], SRV[0], q), lerp(A[1], SRV[1] - 85, q) - math.sin(q * math.pi) * 20
    q = (k - .5) / .5; return lerp(SRV[0], B[0], q), lerp(SRV[1] - 85, B[1], q) - math.sin(q * math.pi) * 20

random.seed(7)
TRAFFIC = []
for n in range(200):
    i, j = random.sample(range(9), 2)
    TRAFFIC.append((n * 0.55, i, j))

def traffic(d, t, t0, t1=1e9, exclude=(), dur=2.2):
    for st, i, j in TRAFFIC:
        st += t0
        if st > t1 or not (st <= t < st + dur + .4): continue
        if i in exclude or j in exclude: continue
        k = (t - st) / dur
        A, B = USERS[i], USERS[j]
        if k < 1:
            x, y = via((A[0], A[1] - 70), (B[0], B[1] - 70), ease(k))
            chip(d, x, y, min(1, k * 6) * (1 if k < .9 else (1 - k) * 10 + .0))
        else:
            plain_msg(d, B[0], B[1] - 70, 1 - (k - 1) / (.4 / dur))

def banner(d, t, n, title):
    a = P(t, .1, .6)
    if n:
        d.rounded_rectangle([60, 36, 160, 66], radius=15, fill=fade(TEAL, a))
        text(d, (110, 51), f"STEP {n}", 15, BG if a > .5 else fade(BG, a), 1, "Bold", "mm")
    text(d, (180 if n else 60, 51 + (1 - a) * 8), title, 28, TEXT, a, "Bold", "lm")

def caption(d, t, t0, s, col=TEXT, y=665, size=23, t1=None):
    a = P(t, t0, t0 + .5)
    if t1 is not None: a *= 1 - P(t, t1, t1 + .4)
    if a <= .01: return
    f = font(size, "Medium"); tw = f.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 20, y - 22, W / 2 + tw / 2 + 20, y + 22], radius=12, fill=fade((22, 30, 50), a))
    text(d, (W // 2, y), s, size, col, a, "Medium", "mm")

def tag(d, x, y, s, col, a, size=15, anchor="mm"):
    text(d, (x, y), s, size, col, a, "SemiBold", anchor)

# ---------- scenes ----------
def s0(d, t):
    lock(d, W // 2, 200, 50, TEAL, P(t, .2, .8))
    a = P(t, .6, 1.4)
    text(d, (W // 2, 320 + (1 - a) * 16), "How targeted chat scanning", 54, TEXT, a, "ExtraBold", "mm")
    text(d, (W // 2, 386 + (1 - a) * 16), "would work", 54, TEXT, a, "ExtraBold", "mm")
    text(d, (W // 2, 470), "A system where nobody is scanned by default", 24, AMBER, P(t, 1.8, 2.5), "Medium", "mm")

def s1(d, t):
    banner(d, t, 1, "Everyone is protected by default")
    users(d, stagger_t=t, locks=1)
    world_server(d, P(t, .6, 1.2))
    actors(d, {}, P(t, 1.2, 2.0))
    traffic(d, t, 2.2)
    a = P(t, 4.0, 4.6)
    tag(d, SRV[0], SRV[1] - 150, "sees only scrambled data", AMBER, a, 17)
    caption(d, t, 5.0, "End-to-end encryption for everyone. Nobody's chats are scanned.")

def s2(d, t):
    banner(d, t, 2, "Concrete evidence about one person")
    sk = P(t, 3.6, 4.4)
    users(d, sus=sk)
    world_server(d)
    actors(d, {"police": P(t, 1.6, 2.2)})
    traffic(d, t, -6, exclude=())
    k = P(t, .4, 1.9)
    if k < 1:
        x, y = lerp(1300, ACT["police"][0] - 40, k), lerp(70, ACT["police"][1] - 40, k)
        document(d, x, y, 40, TEXT, 1); tag(d, x, y - 36, "evidence / report", TEXT, P(t, .4, .8))
    pa = P(t, 2.6, 3.4)
    if pa > 0:
        px, py = ACT["police"][0] - 90, ACT["police"][1] + 20
        sx, sy = USERS[SUS][0] + 36, USERS[SUS][1] - 30
        arrow(d, px, py, lerp(px, sx, pa), lerp(py, sy, pa), AMBER, 1, 3, dash=10)
    caption(d, t, 4.6, "Real evidence points to one person, not profiling, not a guess.")

def s3(d, t):
    banner(d, t, 3, "Ordinary methods are tried first")
    users(d, sus=1)
    world_server(d)
    actors(d, {"police": 1})
    traffic(d, t, -12)
    pa = P(t, .4, 1.6)
    px, py = ACT["police"][0] - 90, ACT["police"][1]
    arrow(d, px, py, lerp(px, SRV[0] + 80, pa), lerp(py, SRV[1] - 60, pa), (110, 150, 245), pa, 3, dash=10)
    tag(d, 790, 270, "wiretap", (110, 150, 245), P(t, .8, 1.3), 16)
    k = P(t, 2.0, 3.4)
    if t > 2.0:
        x, y = lerp(SRV[0] + 40, ACT["police"][0] - 30, k), lerp(SRV[1] - 110, ACT["police"][1] - 100, k)
        chip(d, x, y, 1)
        cross(d, x, y, 34, CORAL, P(t, 3.6, 4.0))
        tag(d, x, y - 34, "unreadable", CORAL, P(t, 3.6, 4.0), 16)
    caption(d, t, 4.4, "On encrypted apps a wiretap sees only scrambled data, so it fails.")

def s4(d, t):
    banner(d, t, 4, "An impartial judge checks the case")
    users(d, sus=1)
    world_server(d)
    actors(d, {"police": 1 - P(t, 1.6, 2.2), "judge": P(t, 1.2, 1.8)})
    traffic(d, t, -18)
    k = P(t, .4, 1.6)
    if k < 1:
        x = lerp(ACT["police"][0] + 40, ACT["judge"][0] - 40, k); y = ACT["police"][1] - 90 - math.sin(k * math.pi) * 20
        document(d, x, y, 36, TEXT, 1); tag(d, x, y - 32, "request", TEXT, 1)
    jx, jy = ACT["judge"]
    items = ["Concrete evidence", "Last resort", "Proportionate"]
    oa = P(t, 6.0, 6.6)
    for i, s in enumerate(items):
        a = P(t, 2.2 + i * .9, 2.6 + i * .9) * (1 - oa)
        y = 315 + i * 40
        d.rounded_rectangle([1035, y - 15, 1065, y + 15], radius=6, outline=fade(MUTED, a), width=2)
        check(d, 1050, y, 20, GREEN, a, P(t, 2.6 + i * .9, 3.0 + i * .9))
        text(d, (1078, y), s, 18, TEXT, a, "SemiBold", "lm")
    if oa > 0:
        ox, oy = 1140, 380
        d.rounded_rectangle([ox - 110, oy - 70, ox + 110, oy + 76], radius=12, fill=fade((40, 36, 28), oa), outline=fade(AMBER, oa), width=3)
        text(d, (ox, oy - 48), "COURT ORDER", 17, AMBER, oa, "Bold", "mm")
        for i, s in enumerate(["1 person only", "named content only", "30 days"]):
            text(d, (ox - 90, oy - 14 + i * 28), "•  " + s, 16, TEXT, oa, "Medium", "lm")
    caption(d, t, 3.8, "Before any scanning: is there evidence, is it a last resort, is it proportionate?", t1=6.6)
    caption(d, t, 7.0, "Approved for one person, limited content, limited time.")

def s5(d, t):
    banner(d, t, 5, "The provider activates the check on one phone")
    users(d, sus=1, scan=P(t, 3.6, 4.2))
    world_server(d)
    actors(d, {"judge": 1 - P(t, 1.8, 2.4)})
    traffic(d, t, -24, exclude=(SUS,))
    k = P(t, .3, 1.8)
    if k < 1:
        x = lerp(ACT["judge"][0], SRV[0] + 30, k); y = lerp(ACT["judge"][1] - 90, SRV[1] - 110, k) - math.sin(k * math.pi) * 40
        document(d, x, y, 34, AMBER, 1); tag(d, x, y - 30, "order", AMBER, 1)
    k2 = P(t, 2.2, 3.6)
    if 2.2 < t < 3.7:
        x, y = lerp(SRV[0] - 60, USERS[SUS][0], k2), lerp(SRV[1], USERS[SUS][1] - 3, k2)
        magnifier(d, x, y, 14, AMBER, 1)
    if t > 4.2:
        x, y = USERS[SUS]
        a = P(t, 4.2, 4.8)
        d.rounded_rectangle([x - 30, y + 60, x + 30, y + 66], radius=3, fill=fade(AMBER, a))
        tag(d, x, y + 82, "30 days", AMBER, a, 14)
    caption(d, t, 4.6, "Only the suspect's phone gets the check. Everyone else stays fully encrypted.")

def s6(d, t):
    banner(d, t, 6, "Messages are checked on the phone")
    users(d, sus=1, scan=1, slabel=1 - P(t, 0, .4))
    world_server(d)
    act = {"review": P(t, 10.0, 10.5) * (1 - P(t, 13.0, 13.5)), "police": P(t, 12.8, 13.3)}
    actors(d, act)
    traffic(d, t, -30, exclude=(SUS, 0, 2))
    x, y = USERS[SUS]
    bx, by = x, y - 82
    d.rounded_rectangle([x - 30, y + 60, x + 30, y + 66], radius=3, fill=fade(LINE, 1))
    d.rounded_rectangle([x - 30, y + 60, x - 30 + 60 * lerp(1, .55, clamp(t / 14)), y + 66], radius=3, fill=fade(AMBER, 1))
    # A: suspect sends normal message
    if .4 < t < 4.8:
        if t < 2.6:
            plain_msg(d, bx, by, P(t, .4, .8))
            magnifier(d, bx + math.sin((t - .9) * 5) * 18 - 4, by, 13, AMBER, P(t, .9, 1.1) * (1 - P(t, 1.9, 2.1)))
            check(d, bx + 40, by, 18, GREEN, P(t, 2.0, 2.2), P(t, 2.0, 2.4))
        else:
            k = P(t, 2.6, 4.6); A = (bx, by); B = (USERS[0][0], USERS[0][1] - 70)
            px, py = via(A, B, k); chip(d, px, py, 1)
    tag(d, 245, 120, "no match: nothing reported, nobody reads it", GREEN, P(t, 2.0, 2.4) * (1 - P(t, 4.4, 4.8)), 16)
    # B: contact sends to suspect
    if 5.0 < t < 8.8:
        if t < 6.8:
            k = P(t, 5.0, 6.8); px, py = via((USERS[2][0], USERS[2][1] - 70), (bx, by), k); chip(d, px, py, 1)
        else:
            plain_msg(d, bx, by, 1 - P(t, 8.4, 8.8))
            magnifier(d, bx + math.sin((t - 6.9) * 5) * 18 - 4, by, 13, AMBER, P(t, 6.9, 7.1) * (1 - P(t, 7.8, 8.0)))
            check(d, bx + 40, by, 18, GREEN, P(t, 7.9, 8.1) * (1 - P(t, 8.4, 8.8)), P(t, 7.9, 8.3))
    tag(d, 245, 120, "contacts' messages: checked locally, never read by people", GREEN, P(t, 7.9, 8.3) * (1 - P(t, 8.8, 9.2)), 16)
    # C: match
    if 9.0 < t:
        if t < 10.2:
            match_item(d, bx, by, P(t, 9.0, 9.3))
            magnifier(d, bx + math.sin((t - 9.3) * 5) * 14 - 4, by, 13, AMBER, P(t, 9.3, 9.5) * (1 - P(t, 9.9, 10.1)))
        else:
            match_item(d, bx, by, 1 - P(t, 13.4, 13.9))
        fa = P(t, 10.0, 10.3) * (1 - P(t, 13.4, 13.9))
        d.line([(bx + 34, by + 18), (bx + 34, by - 22)], fill=fade(CORAL, fa), width=3)
        d.polygon([(bx + 36, by - 22), (bx + 54, by - 16), (bx + 36, by - 10)], fill=fade(CORAL, fa))
        tag(d, 245, 120, "match with content named in the order", CORAL, fa, 16)
        k = P(t, 10.4, 11.8)
        if 10.4 < t < 13.0:
            rx, ry = ACT["review"]
            px, py = lerp(bx + 20, rx - 100, k), lerp(by, ry - 20, k) - math.sin(k * math.pi) * 60
            if k < 1: document(d, px, py, 30, CORAL, 1)
        rx, ry = ACT["review"]
        check(d, rx + 60, ry - 40, 22, GREEN, P(t, 12.0, 12.2), P(t, 12.0, 12.5))
        pk = P(t, 12.6, 13.4)
        if pk > 0:
            arrow(d, rx, ry - 64, rx, lerp(ry - 64, ACT["police"][1] + 66, pk), CORAL, 1, 3, dash=8)
    caption(d, t, 0.6, "Every message is checked on the phone against the order's list.", t1=8.6)
    caption(d, t, 9.6, "Only a match is reported, and a human confirms it before police see it.")

def s7(d, t):
    banner(d, t, 7, "Time limits, oversight and appeal")
    off = P(t, 3.2, 4.0)
    users(d, sus=1 - P(t, 3.8, 4.6), scan=1 - off, slabel=0)
    world_server(d)
    actors(d, {"audit": P(t, 4.6, 5.2), "judge": P(t, 7.4, 8.0)})
    traffic(d, t, -40)
    x, y = USERS[SUS]
    lv = lerp(.55, 0, P(t, .4, 3.0))
    a = 1 - P(t, 3.4, 4.0)
    d.rounded_rectangle([x - 30, y + 60, x + 30, y + 66], radius=3, fill=fade(LINE, a))
    if lv > .01: d.rounded_rectangle([x - 30, y + 60, x - 30 + 60 * lv, y + 66], radius=3, fill=fade(AMBER, a))
    tag(d, x, y + 82, "expired" if t > 3.0 else "", CORAL, a, 14)
    tag(d, 245, 120, "order expires: the check is removed", TEAL, P(t, 3.2, 3.6) * (1 - P(t, 6.6, 7.0)), 16)
    ax, ay = ACT["audit"]
    la = P(t, 5.0, 5.6)
    if la > 0:
        d.rounded_rectangle([ax - 140, ay - 205, ax + 100, ay - 85], radius=10, fill=fade(PANEL, la), outline=fade(LINE, la), width=2)
        for i, s in enumerate(["Order #127 · 1 person", "30 days · 1 report", "Published in yearly stats"]):
            text(d, (ax - 124, ay - 182 + i * 32), s, 16, TEXT if i < 2 else TEAL, P(t, 5.2 + i * .4, 5.6 + i * .4), "Medium", "lm")
    pk = P(t, 7.0, 8.0)
    if pk > 0:
        sx, sy = x + 34, y - 40
        jx, jy = ACT["judge"][0] - 60, ACT["judge"][1] + 66
        arrow(d, sx, sy, lerp(sx, jx, pk), lerp(sy, jy, pk), AMBER, 1, 3, dash=10)
        tag(d, 560, 205, "right to appeal", AMBER, P(t, 7.6, 8.0), 16)
    caption(d, t, 1.0, "The order runs out after a fixed time.", t1=4.6)
    caption(d, t, 5.0, "Every case is logged, counted publicly, and can be appealed.")

def s8(d, t):
    a = P(t, .3, 1.1)
    text(d, (W // 2, 290 + (1 - a) * 16), "Never for everyone.", 64, TEXT, a, "ExtraBold", "mm")
    b = P(t, 1.3, 2.1)
    text(d, (W // 2, 380 + (1 - b) * 16), "Only for a suspect, under a judge.", 46, AMBER, b, "Bold", "mm")
    lock(d, W // 2, 180, 44, TEAL, P(t, .1, .6))

SCENES = [("s0", s0, 5), ("s1", s1, 10), ("s2", s2, 8), ("s3", s3, 7), ("s4", s4, 10.5), ("s5", s5, 8),
          ("s6", s6, 15), ("s7", s7, 10), ("s8", s8, 6)]
FADE = {"s0": (0.5, 0.5), "s1": (0.5, 0), "s7": (0, 0.6), "s8": (0.5, 1.2)}

def frame(name, fn, t, dur):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    fn(d, t)
    fi, fo = FADE.get(name, (0, 0))
    f = 1.0
    if fi: f = min(f, clamp(t / fi))
    if fo: f = min(f, clamp((dur - t) / fo))
    if f < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, f)
    return im

if __name__ == "__main__":
    out, mode = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    if mode == "stills":
        picks = {"s1": [7], "s2": [6], "s3": [5], "s4": [3.5, 8], "s5": [6], "s6": [1.5, 7.5, 11, 13.5], "s7": [6, 9]}
        for name, fn, dur in SCENES:
            for tt in picks.get(name, []):
                frame(name, fn, tt, dur).save(f"{out}/{name}_{tt}.png")
    else:
        only = sys.argv[3:] or [n for n, _, _ in SCENES]
        for name, fn, dur in SCENES:
            if name not in only: continue
            tmp = f"{out}/{name}.tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                  "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                                  "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for i in range(int(round(dur * FPS))):
                p.stdin.write(frame(name, fn, i / FPS, dur).tobytes())
            p.stdin.close()
            if p.wait() == 0: os.rename(tmp, f"{out}/{name}.mp4")
            print(name, "done", flush=True)
