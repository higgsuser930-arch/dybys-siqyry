#!/usr/bin/env python3
"""TTS жеке [ү] [ұ] [ө] [қ] [ғ] [ң] [һ] [о] [щ] дыбысын сенімді айта алмайды (STT-пен расталмайды).
Сондықтан бұл дыбыстар үшін аудио = «дыбыс + осы дыбыс бар таныс сөз» («Ү. Үй.»); сөздің дұрыс айтылғанын STT тексереді.
Нақты жазылған жеке дыбыс файлы болса, audio/manifest.js ішіндегі 'snd:<әріп>' мәнін соған ауыстырыңыз."""
import json, os, sys, re
sys.argv = ['x', 'zzz']
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(f'{ROOT}/tools/gen_sounds.py', encoding='utf8').read().split('os.makedirs(')[0]
ns = {'__file__': f'{ROOT}/tools/gen_sounds.py'}; exec(compile(src, 'gs', 'exec'), ns)
WORD = {'о': 'от', 'ө': 'өрік', 'ұ': 'ұя', 'ү': 'үй', 'ғ': 'ғалым', 'қ': 'қала', 'ң': 'аң', 'һ': 'қаһар', 'щ': 'щетка'}
norm = lambda t: re.sub(r'[^а-яәғқңөұүһіё]', '', t.lower())
mp = f'{ROOT}/audio/manifest.js'
mf = json.loads(open(mp, encoding='utf8').read().split('=', 1)[1].strip().rstrip(';'))
for x, w in WORD.items():
    best = None
    for v in ns['VOICES']:
        for text in (f'{x.upper()}. {w.capitalize()}.', f'{x.upper()}... {w}.'):
            try: mp3 = ns['tts'](text, v); t, d = ns['stt'](mp3)
            except Exception as e: print('ERR', x, text, str(e)[:40]); continue
            ok = ns['norm'](t).endswith(norm(w)) or norm(w) in norm(t) or (x == 'қ' and norm(t).endswith('кала'))  # STT қ мен к-ны айыра бермейді
            print(x, v[:4], repr(text), '->', repr(t), 'OK' if ok else '--', flush=True)
            if ok and (best is None or best[1] < 1): best = (mp3, 1, text); break
        if best: break
    if best:
        open(f'{ROOT}/audio/{ns["fn"]("snd:" + x)}', 'wb').write(best[0]); mf['snd:' + x] = ns['fn']('snd:' + x)
    else: print('!!! жоқ:', x)
open(mp, 'w', encoding='utf8').write('window.AUDIO_MANIFEST = ' + json.dumps(mf, ensure_ascii=False) + ';\n')
