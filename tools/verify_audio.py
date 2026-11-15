#!/usr/bin/env python3
"""Сөз аудиоларын STT-пен тексеріп, айтылуы сәйкес келмегендерін басқа дауыспен қайта жасайды."""
import json, os, sys, re, concurrent.futures as cf
sys.argv = ['x', 'zzz']
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(f'{ROOT}/tools/gen_sounds.py', encoding='utf8').read().split('os.makedirs(')[0]
ns = {'__file__': f'{ROOT}/tools/gen_sounds.py'}; exec(compile(src, 'gs', 'exec'), ns)
L = {'ә': 'а', 'ө': 'о', 'ү': 'у', 'ұ': 'у', 'і': 'и', 'ы': 'и', 'қ': 'к', 'ғ': 'г', 'ң': 'н', 'һ': 'х', 'э': 'е', 'щ': 'ш', 'й': 'и', 'ё': 'е'}
loose = lambda s: ''.join(L.get(c, c) for c in re.sub(r'[^а-яәғқңөұүһіё]', '', s.lower()))
def lev(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]
mp = f'{ROOT}/audio/manifest.js'
mf = json.loads(open(mp, encoding='utf8').read().split('=', 1)[1].strip().rstrip(';'))
keys = [k for k in mf if ':' not in k]
def good(k, mp3):
    t, d = ns['stt'](mp3); a, b = loose(t), loose(k)
    return lev(a, b) <= (0 if len(b) <= 3 else 1), t
def chk(k):
    path = f'{ROOT}/audio/{mf[k]}'
    try: ok, t = good(k, open(path, 'rb').read())
    except Exception as e: return k, 'ERR', str(e)[:30]
    if ok: return k, 'ok', t
    for v in ns['VOICES']:
        for txt in (k + '.', k.capitalize() + '.'):
            try: m = ns['tts'](txt, v); ok2, t2 = good(k, m)
            except Exception: continue
            if ok2: open(path, 'wb').write(m); return k, 'FIXED', f'{t} -> {t2}'
    return k, 'BAD', t
bad = 0
with cf.ThreadPoolExecutor(4) as ex:
    for k, st, t in ex.map(chk, keys):
        if st != 'ok': print(st, k, t, flush=True); bad += st in ('BAD', 'ERR')
print('DONE', len(keys), 'bad', bad)
