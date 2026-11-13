#!/usr/bin/env python3
"""cues.json을 읽어 장면 전환에 맞춘 음악과 효과음을 합성하고 48kHz 스테레오 WAV로 쓴다.

외부 패키지 없이 표준 라이브러리만 쓴다. 측정: 30초, 큐 25개 기준 약 4초 걸린다(Apple Silicon Mac).

cues.json 형식 (render.mjs --dump-cues 가 window.__reel.cues / music 에서 만든다):
{
  "duration": 15,
  "music": {
    "bpm": 120, "key": "A", "scale": "minor",          # key: C C# D ... B, scale: minor | major
    "progression": [0, 5, 3, 4],                         # 음계 도수(0부터), 한 마디에 하나
    "sections": [                                        # 구간별로 켤 악기
      {"from": 0,  "to": 2,  "pad": true},
      {"from": 2,  "to": 12, "kick": true, "hat": true, "bass": true, "pad": true, "clap": true},
      {"from": 12, "to": 13, "pad": true},
      {"from": 13, "to": 15, "kick": true, "bass": true, "pad": true}
    ],
    "gain": 0.8,
    "energy": "mid"                                      # low | mid | high. 아래 ENERGY 표 참고
  },
  "cues": [
    {"t": 0.0,  "type": "impact"},
    {"t": 1.0,  "type": "riser", "len": 1.0},           # len 동안 상승하고 t+len 에서 끝난다
    {"t": 2.0,  "type": "whoosh", "len": 0.5},
    {"t": 3.1,  "type": "tick", "pitch": 1.5},
    {"t": 4.0,  "type": "glitch", "len": 0.25},
    {"t": 5.0,  "type": "blip", "pitch": 1.0},
    {"t": 6.0,  "type": "type", "len": 0.6},            # 타이핑 소리 연속
    {"t": 7.0,  "type": "downlifter", "len": 0.8},
    {"t": 8.0,  "type": "swoosh_rev", "len": 0.6},       # 역재생 느낌의 흡입음, t+len 에서 끝난다
    {"t": 13.0, "type": "boom"},
    {"t": 14.0, "type": "kick"}
  ]
}
큐 종류: impact, boom, riser, downlifter, whoosh, swoosh_rev, blip, tick, glitch, type, kick.
각 큐는 선택 키 gain(기본 1.0), pan(-1..1)을 받는다.
"""
import argparse
import json
import math
import random
import struct
import wave

SR = 48000
# 음악 강도. low: 킥은 2박마다 작게, 클랩 없음, 패드 중심. mid: 킥 매 박, 클랩 약하게. high: 전부 크게.
# sfx 는 효과음 전체 배율, heavy 는 impact/boom/glitch 에만 추가로 곱하는 배율이다.
ENERGY = {
    'low':  {'kick': 0.45, 'kick_every': 8, 'clap': 0.0,  'hat': 0.10, 'bass': 0.35, 'pad': 0.45, 'sfx': 0.6, 'heavy': 0.5},
    'mid':  {'kick': 0.65, 'kick_every': 4, 'clap': 0.25, 'hat': 0.16, 'bass': 0.42, 'pad': 0.38, 'sfx': 0.8, 'heavy': 0.7},
    'high': {'kick': 0.9,  'kick_every': 4, 'clap': 0.45, 'hat': 0.22, 'bass': 0.5,  'pad': 0.32, 'sfx': 1.0, 'heavy': 1.0},
}
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
NOTE.update({'Db': 1, 'Eb': 3, 'Gb': 6, 'Ab': 8, 'Bb': 10})
SCALES = {'minor': [0, 2, 3, 5, 7, 8, 10], 'major': [0, 2, 4, 5, 7, 9, 11]}


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Mix:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.L = [0.0] * self.n
        self.R = [0.0] * self.n

    def add(self, t, samples, gain=1.0, pan=0.0):
        start = int(t * SR)
        gl = gain * math.cos((pan + 1) * math.pi / 4)
        gr = gain * math.sin((pan + 1) * math.pi / 4)
        L, R, n = self.L, self.R, self.n
        for i, s in enumerate(samples):
            j = start + i
            if j < 0:
                continue
            if j >= n:
                break
            L[j] += s * gl
            R[j] += s * gr


def noise(rng, n):
    return [rng.uniform(-1, 1) for _ in range(n)]


def svf(x, cutoff_fn, q=0.7, mode='bp'):
    """TPT state-variable filter (Zavalishin). 차단 주파수와 무관하게 안정하다. cutoff_fn(i) -> Hz."""
    ic1 = ic2 = 0.0
    k = 1.0 / max(q, 0.1)
    out = []
    for i, s in enumerate(x):
        g = math.tan(math.pi * min(max(cutoff_fn(i), 20.0), SR * 0.45) / SR)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = s - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        out.append(v1 if mode == 'bp' else v2 if mode == 'lp' else s - k * v1 - v2)
    return out


# ---------- 악기 ----------

def kick(length=0.38):
    n = int(length * SR)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = 45 + 110 * math.exp(-t * 30)
        ph += 2 * math.pi * f / SR
        env = math.exp(-t * 7.5)
        click = math.exp(-t * 400) * 0.6
        out.append(math.tanh(1.6 * math.sin(ph) * env) + click * math.sin(ph * 3))
    return out


def clap(rng):
    n = int(0.22 * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 1600, q=1.2)
    out = []
    for i, s in enumerate(y):
        t = i / SR
        # 손뼉 특유의 짧은 반복 어택
        env = sum(math.exp(-(t - d) * 90) for d in (0, 0.011, 0.022) if t >= d) * 0.5 + math.exp(-t * 18) * 0.6
        out.append(s * env * 2.2)
    return out


def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 9000, q=0.6, mode='hp')
    k = 14 if open_ else 70
    return [s * math.exp(-(i / SR) * k) * 0.8 for i, s in enumerate(y)]


def bass(freq, length):
    n = int(length * SR)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        ph += 2 * math.pi * freq / SR
        s = math.sin(ph) + 0.35 * math.sin(2 * ph) + 0.12 * math.sin(3 * ph)
        env = min(1, t / 0.005) * math.exp(-t * 2.2) * min(1, (length - t) / 0.02)
        out.append(math.tanh(s * 1.3) * env)
    return out


def pad(freqs, length, detune=0.004):
    n = int(length * SR)
    L, R = [0.0] * n, [0.0] * n
    atk, rel = min(0.4, length / 3), min(0.5, length / 3)
    for f in freqs:
        for side, d in ((L, 1 - detune), (R, 1 + detune)):
            w = 2 * math.pi * f * d / SR
            for i in range(n):
                side[i] += math.sin(w * i) + 0.2 * math.sin(2 * w * i)
    out_env = []
    for i in range(n):
        t = i / SR
        out_env.append(min(1, t / atk) * min(1, (length - t) / rel) / max(1, len(freqs)))
    return [a * e for a, e in zip(L, out_env)], [b * e for b, e in zip(R, out_env)]


def riser(rng, length):
    n = int(length * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 300 * (20 ** (i / n)), q=3)
    out, ph = [], 0.0
    for i, s in enumerate(y):
        p = i / n
        ph += 2 * math.pi * (180 * (6 ** p)) / SR
        env = p ** 2
        out.append((s * 1.4 + 0.25 * math.sin(ph)) * env)
    return out


def downlifter(rng, length):
    return list(reversed(riser(rng, length)))


def whoosh(rng, length):
    n = int(length * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 400 + 4000 * math.sin(math.pi * i / n), q=1.5)
    return [s * math.sin(math.pi * i / n) ** 2 * 1.6 for i, s in enumerate(y)]


def swoosh_rev(rng, length):
    n = int(length * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 300 + 6000 * (i / n) ** 2, q=2)
    return [s * (i / n) ** 3 * 2.0 for i, s in enumerate(y)]


def impact(rng, length=1.4):
    n = int(length * SR)
    k = kick(0.5)
    x = noise(rng, int(0.6 * SR))
    nz = svf(x, lambda i: 1200 * math.exp(-i / SR * 5) + 120, q=0.8, mode='lp')
    out = []
    for i in range(n):
        t = i / SR
        sub = math.sin(2 * math.pi * 48 * t) * math.exp(-t * 2.5)
        s = sub * 0.9
        if i < len(k):
            s += k[i]
        if i < len(nz):
            s += nz[i] * math.exp(-t * 6) * 1.5
        out.append(math.tanh(s))
    return out


def boom(rng):
    return impact(rng, 2.2)


def blip(pitch=1.0, length=0.07):
    n = int(length * SR)
    f = 1200 * pitch
    return [math.sin(2 * math.pi * f * i / SR) * math.exp(-(i / SR) * 60) for i in range(n)]


def tick(rng, pitch=1.0):
    n = int(0.03 * SR)
    x = noise(rng, n)
    y = svf(x, lambda i: 3500 * pitch, q=4)
    return [s * math.exp(-(i / SR) * 200) * 3 for i, s in enumerate(y)]


def glitch(rng, length):
    n = int(length * SR)
    out, hold, val = [], 0, 0.0
    for i in range(n):
        if hold <= 0:
            hold = rng.randint(30, 900)
            val = rng.choice([-1, 1]) * rng.uniform(0.2, 0.9)
            if rng.random() < 0.3:
                val = 0
        hold -= 1
        out.append(val * (1 if (i // rng.randint(20, 80)) % 2 else 0.6))
    return [s * 0.5 for s in out]


def typing(rng, length):
    n = int(length * SR)
    out = [0.0] * n
    t = 0.0
    while t < length:
        clk = tick(rng, rng.uniform(0.8, 1.4))
        s = int(t * SR)
        for i, v in enumerate(clk):
            if s + i < n:
                out[s + i] += v * 0.7
        t += rng.uniform(0.045, 0.09)
    return out


# ---------- 조립 ----------

def build(spec, seed=7):
    rng = random.Random(seed)
    dur = float(spec.get('duration', 15))
    mix = Mix(dur + 1.5)
    music = spec.get('music')
    en = ENERGY.get((music or {}).get('energy', 'mid'), ENERGY['mid'])

    if music:
        bpm = float(music.get('bpm', 120))
        beat = 60.0 / bpm
        bar = beat * 4
        root = NOTE.get(music.get('key', 'A'), 9) + 36  # 베이스 옥타브
        scale = SCALES.get(music.get('scale', 'minor'), SCALES['minor'])
        prog = music.get('progression', [0, 5, 3, 4])
        g = float(music.get('gain', 0.8))
        sections = music.get('sections', [{'from': 0, 'to': dur, 'kick': True, 'hat': True, 'bass': True, 'pad': True}])

        def degree(d, octave=0):
            return root + scale[d % 7] + 12 * (d // 7) + 12 * octave

        def on(t, inst):
            for s in sections:
                if s['from'] - 1e-6 <= t < s['to'] - 1e-6 and s.get(inst):
                    return True
            return False

        kick_s = kick()
        steps = int(dur / (beat / 4)) + 1
        for k in range(steps):
            t = k * beat / 4
            if t >= dur:
                break
            b16 = k % 16
            if b16 % en['kick_every'] == 0 and on(t, 'kick'):
                mix.add(t, kick_s, en['kick'] * g)
            if b16 in (4, 12) and en['clap'] > 0 and on(t, 'clap'):
                mix.add(t, clap(rng), en['clap'] * g, 0.05)
            if b16 % 2 == 1 and on(t, 'hat'):
                mix.add(t, hat(rng, open_=(b16 % 8 == 7)), en['hat'] * g, 0.3 if b16 % 4 == 1 else -0.3)
            if b16 % 2 == 0 and on(t, 'bass'):
                d = prog[int(t / bar) % len(prog)]
                f = mtof(degree(d) + (12 if b16 % 8 == 6 else 0))
                mix.add(t, bass(f, beat / 2 * 0.9), en['bass'] * g)
        # 패드: 한 마디 단위 화음
        nbars = int(math.ceil(dur / bar))
        for b in range(nbars):
            t = b * bar
            # 구간 경계에서 끊기도록 마디를 잘게 나눠 검사한다
            seg_start = None
            for q in range(17):
                tt = min(t + q * bar / 16, dur)
                active = q < 16 and tt < dur and on(tt, 'pad')
                if active and seg_start is None:
                    seg_start = tt
                if (not active) and seg_start is not None:
                    d = prog[b % len(prog)]
                    freqs = [mtof(degree(d + x, 2)) for x in (0, 2, 4)]
                    Lp, Rp = pad(freqs, tt - seg_start)
                    mix.add(seg_start, Lp, en['pad'] * g, -1)
                    mix.add(seg_start, Rp, en['pad'] * g, 1)
                    seg_start = None

    for c in spec.get('cues', []):
        t = float(c['t'])
        ty = c['type']
        ln = float(c.get('len', 0.5))
        g = float(c.get('gain', 1.0))
        pan = float(c.get('pan', 0.0))
        pitch = float(c.get('pitch', 1.0))
        if ty == 'impact':
            s, g0 = impact(rng), 0.9
        elif ty == 'boom':
            s, g0 = boom(rng), 1.0
        elif ty == 'riser':
            s, g0 = riser(rng, ln), 0.5
        elif ty == 'downlifter':
            s, g0 = downlifter(rng, ln), 0.4
        elif ty == 'whoosh':
            s, g0 = whoosh(rng, ln), 0.6
        elif ty == 'swoosh_rev':
            s, g0 = swoosh_rev(rng, ln), 0.5
        elif ty == 'blip':
            s, g0 = blip(pitch), 0.3
        elif ty == 'tick':
            s, g0 = tick(rng, pitch), 0.4
        elif ty == 'glitch':
            s, g0 = glitch(rng, ln), 0.35
        elif ty == 'type':
            s, g0 = typing(rng, ln), 0.35
        elif ty == 'kick':
            s, g0 = kick(), 0.9
        else:
            print(f'알 수 없는 큐 종류 {ty}를 건너뛴다.')
            continue
        if ty in ('impact', 'boom', 'glitch'):
            g0 *= en['heavy']
        mix.add(t, s, g0 * g * en['sfx'], pan)
    return mix, dur


def master(mix, dur, out_path):
    # 영상 길이와 정확히 같게 자른다. 렌더러가 -shortest 로 맞추므로 더 길게 쓰면 페이드가 잘린다.
    n = int(dur * SR)
    L, R = mix.L[:n], mix.R[:n]
    peak = max(1e-9, max(max(abs(x) for x in L), max(abs(x) for x in R)))
    drive = 1.4 / peak
    L = [math.tanh(x * drive) for x in L]
    R = [math.tanh(x * drive) for x in R]
    peak = max(max(abs(x) for x in L), max(abs(x) for x in R), 1e-9)
    norm = 0.89 / peak  # 약 -1 dBFS
    fade = int(0.3 * SR)  # 마지막 0.3초 페이드 아웃
    with wave.open(out_path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(n):
            f = min(1.0, (n - i) / fade)
            frames += struct.pack('<hh', int(L[i] * norm * f * 32767), int(R[i] * norm * f * 32767))
        w.writeframes(bytes(frames))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cues')
    ap.add_argument('-o', '--out', default='audio.wav')
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    with open(a.cues) as f:
        spec = json.load(f)
    mix, dur = build(spec, a.seed)
    master(mix, dur, a.out)
    with wave.open(a.out) as w:
        real = w.getnframes() / w.getframerate()
    print(f'{a.out} ({real:.2f}초, 큐 {len(spec.get("cues", []))}개)')


if __name__ == '__main__':
    main()
