#!/usr/bin/env python3
"""Жеке дыбыстардың ([а], [ә], [ш]…) аудиосын ElevenLabs TTS арқылы жасап, STT (scribe) арқылы тексереді.
Нәтиже: audio/<sha1(key+VER)>.mp3, audio/manifest.js жаңартылады. Қолдану: python3 tools/gen_sounds.py [әріптер...]"""
import json, hashlib, os, sys, re, time, urllib.request, uuid, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = 'v2'
VOICES = ['21m00Tcm4TlvDq8ikWAM', 'EXAVITQu4vr4xnSDxMaL', 'pNInz6obpgDQGcFmaJgB']
raw = open(f'{ROOT}/data/album-data.js', encoding='utf8').read()
D = json.loads(raw[raw.index('=') + 1:].strip().rstrip(';'))
need = set()
for s in D:
    need |= set(s['g1']['easy'] + s['g1']['medium']) | {s['letter'].lower()}
if len(sys.argv) > 1: need &= set(sys.argv[1:])
VOW = set('аәоөыіұүеэиу')
def cands(x):
    X = x.upper()
    if x in VOW:
        return [f'{X}.', f'{X}! {X}!', f'{x}{x}{x}.', f'«{X}» дыбысы.', f'{X}-{x}-{x}.']
    stops = set('бгдкқпт цч')
    return [f'{x}{x}{x}.', f'{X}.', f'{X}-{x}-{x}.', f'{x}ы.', f'{x}ә.', f'«{X}» дыбысы.']
def fn(key): return hashlib.sha1((key + VER).encode()).hexdigest()[:10] + '.mp3'
def post(url, body, headers, timeout=90):
    for i in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url, body, headers), timeout=timeout).read()
        except Exception as e: err = e; time.sleep(2 + 3 * i)
    raise err
def tts(text, voice):
    b = json.dumps({'text': text, 'model_id': 'eleven_v3', 'language_code': 'kk'}).encode()
    return post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_64', b, {'Content-Type': 'application/json'})
def stt(mp3):
    bd = uuid.uuid4().hex; parts = []
    for k, v in (('model_id', 'scribe_v1'), ('language_code', 'kaz')): parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + mp3 + b'\r\n')
    parts.append(f'--{bd}--\r\n'.encode())
    j = json.loads(post('https://api.elevenlabs.io/v1/speech-to-text', b''.join(parts), {'Content-Type': f'multipart/form-data; boundary={bd}'}))
    return j.get('text', ''), j.get('audio_duration_secs', 0)
def norm(t): return re.sub(r'[^a-zа-яәғқңөұүһіё]', '', t.lower())
def score(x, t):
    n = norm(t)
    if not n: return 0
    if x in VOW: return 2 if set(n) == {x} else (1 if x in n and len(n) <= 2 else 0)
    return 2 if n[0] == x and len(n) <= 3 else (1 if x in n else 0)
def make(x):
    best = (-1, None, None)
    for v in VOICES:
        for c in cands(x):
            try:
                mp3 = tts(c, v); t, dur = stt(mp3)
            except Exception as e: print('ERR', x, c, e, file=sys.stderr); continue
            sc = score(x, t) * 10 + (1 if 0.4 < dur < 3 else 0)
            print(f'  {x}: voice {v[:4]} «{c}» -> «{t}» {dur:.1f}s score {sc}', flush=True)
            if sc > best[0]: best = (sc, mp3, f'{c}|{v[:4]}|{t}')
            if sc >= 21: return x, best
    return x, best
os.makedirs(f'{ROOT}/audio', exist_ok=True)
mf = {}
mpath = f'{ROOT}/audio/manifest.js'
mf = json.loads(open(mpath, encoding='utf8').read().split('=', 1)[1].strip().rstrip(';'))
rep = {}
with cf.ThreadPoolExecutor(3) as ex:
    for x, (sc, mp3, info) in ex.map(make, sorted(need)):
        if mp3:
            open(f'{ROOT}/audio/{fn("snd:" + x)}', 'wb').write(mp3); mf['snd:' + x] = fn('snd:' + x); rep[x] = (sc, info)
open(mpath, 'w', encoding='utf8').write('window.AUDIO_MANIFEST = ' + json.dumps(mf, ensure_ascii=False) + ';\n')
print('\nRESULT'); [print(x, v) for x, v in sorted(rep.items())]
