import numpy as np, wave, sys
SR = 44100
DUR = float(sys.argv[2]); out = sys.argv[1]
N = int(SR * DUR); t = np.arange(N) / SR
BPM = 84; beat = 60 / BPM; bar = 4 * beat
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# Am, F, C, G  (MIDI)
CH = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
ROOT = [45, 41, 48, 43]
chord_len = 2 * bar
L = np.zeros(N); R = np.zeros(N)

def env_seg(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

# pad
nch = int(np.ceil(DUR / chord_len)) + 1
for c in range(nch):
    s0 = int(c * chord_len * SR); n = int((chord_len + 1.2) * SR)
    if s0 >= N: break
    n = min(n, N - s0); tt = np.arange(n) / SR
    e = env_seg(n, 1.0, 1.4)
    notes = CH[c % 4] + [CH[c % 4][0] + 12]
    sig = np.zeros(n)
    for m in notes:
        f = hz(m)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            for h, amp in ((1, 1), (2, .35), (3, .15), (4, .06)):
                sig += amp * np.sin(2 * np.pi * ff * h * tt + h * det * 10)
    sig *= e * 0.018 * (1 + 0.15 * np.sin(2 * np.pi * 0.2 * tt))
    L[s0:s0 + n] += sig; R[s0:s0 + n] += np.roll(sig, 300)

# arp (8ths) from 2.5s
step = beat / 2
k = 0; pos = 0.0
while pos < DUR:
    c = int(pos // chord_len) % 4
    tones = CH[c] + [CH[c][0] + 12, CH[c][1] + 12]
    pat = [0, 2, 1, 3, 2, 4, 3, 2]
    m = tones[pat[k % 8]] + 12
    if pos > 2.5:
        s0 = int(pos * SR); n = min(int(0.9 * SR), N - s0); tt = np.arange(n) / SR
        f = hz(m)
        sig = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 5.5)
        sig *= np.minimum(1, tt / 0.004) * 0.05
        pan = 0.35 if k % 2 else 0.65
        L[s0:s0 + n] += sig * (1 - pan) * 2; R[s0:s0 + n] += sig * pan * 2
    pos += step; k += 1

# bass + soft kick + shaker
pos = 0.0; b = 0
while pos < DUR:
    c = int(pos // chord_len) % 4
    s0 = int(pos * SR)
    if b % 2 == 0 and pos > 5:
        n = min(int(1.3 * beat * SR), N - s0); tt = np.arange(n) / SR
        sig = np.sin(2 * np.pi * hz(ROOT[c] - 12 + 12) * tt) * np.exp(-tt * 2.2) * np.minimum(1, tt / .01) * 0.09
        L[s0:s0 + n] += sig; R[s0:s0 + n] += sig
    if b % 2 == 0 and pos > 10:
        n = min(int(0.35 * SR), N - s0); tt = np.arange(n) / SR
        fk = 50 + 70 * np.exp(-tt * 30)
        sig = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tt * 9) * 0.16
        L[s0:s0 + n] += sig; R[s0:s0 + n] += sig
    if pos > 15:
        so = int((pos + beat / 2) * SR)
        n = min(int(0.08 * SR), N - so)
        if n > 0:
            rng = np.random.default_rng(b)
            nz = rng.standard_normal(n); nz = np.diff(nz, prepend=0)
            sig = nz * np.exp(-np.arange(n) / SR * 60) * 0.012
            L[so:so + n] += sig * .8; R[so:so + n] += sig * 1.2
    pos += beat; b += 1

# simple reverb via FFT convolution with decaying noise
rng = np.random.default_rng(1)
irn = int(1.8 * SR); ir_t = np.arange(irn) / SR
def rev(x, seed):
    ir = np.random.default_rng(seed).standard_normal(irn) * np.exp(-ir_t * 3.2)
    ir[0] = 0
    nfft = 1 << int(np.ceil(np.log2(len(x) + irn)))
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return y / np.max(np.abs(ir)) * 0.004
L = L + rev(L, 2); R = R + rev(R, 3)

st = np.stack([L, R], 1)
fi, fo = int(2 * SR), int(3.5 * SR)
st[:fi] *= np.linspace(0, 1, fi)[:, None]; st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st = st / np.max(np.abs(st)) * 0.5
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", DUR)
