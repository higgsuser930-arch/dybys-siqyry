#!/usr/bin/env python3
"""TTS «әріп аты» ретінде оқи алмайтын дыбыстар ([о] [ө] [ұ] [ү] [ғ] [қ] [ң] [һ] [щ]) үшін:
сөзді TTS-пен (v3, kk) оқытып, with-timestamps арқылы сол дыбыстың таңбасының уақытын алып, ffmpeg-пен кесіп аламыз.
Нәтиже gen_sounds.py сияқты audio/<sha1(key+v2)>.mp3 және manifest.js. Қолдану: python3 tools/slice_sounds.py [әріптер]"""
import json, hashlib, os, sys, base64, subprocess, tempfile, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = 'v2'; VOICE = '21m00Tcm4TlvDq8ikWAM'
# дыбыс: (сөз, таңбаның индексі, созу?)
SLICE = {
    'о': ('от', 0, True), 'ө': ('өрік', 0, True), 'ұ': ('ұн', 0, True), 'ү': ('үй', 0, True),
    'ғ': ('ғарыш', 0, True), 'қ': ('қар', 0, False), 'ң': ('аң', 1, True), 'һ': ('қаһар', 2, True), 'щ': ('борщ', 3, True),
}
def fn(key): return hashlib.sha1((key + VER).encode()).hexdigest()[:10] + '.mp3'
def tts_ts(word):
    b = json.dumps({'text': word, 'model_id': 'eleven_v3', 'language_code': 'kk'}).encode()
    for i in range(4):
        try:
            r = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128', b, {'Content-Type': 'application/json'})
            return json.loads(urllib.request.urlopen(r, timeout=90).read())
        except Exception as e: err = e; time.sleep(2 + 3 * i)
    raise err
def cut(x, word, idx, stretch):
    j = tts_ts(word); al = j['alignment']
    s, e = al['character_start_times_seconds'][idx], al['character_end_times_seconds'][idx]
    s = max(0, s - .02); d = min(max(.12, e - s + .03), .7)
    with tempfile.TemporaryDirectory() as td:
        src, out = f'{td}/a.mp3', f'{td}/o.mp3'; open(src, 'wb').write(base64.b64decode(j['audio_base64']))
        af = ['afade=t=in:d=0.01']
        if stretch and d < .6: af.append(f'atempo={max(.5, d / .6):.3f}')
        if stretch and d < .3: af.append('atempo=0.7')
        dur = d / (max(.5, d / .6) if stretch and d < .6 else 1) / (0.7 if stretch and d < .3 else 1)
        af.append(f'afade=t=out:st={max(0, dur - .05):.3f}:d=0.05'); af.append('volume=1.6')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{s:.3f}', '-t', f'{d:.3f}', '-i', src, '-af', ','.join(af), '-b:a', '64k', out], check=True)
        return open(out, 'rb').read(), (word, s, e, d)
mp = f'{ROOT}/audio/manifest.js'
mf = json.loads(open(mp, encoding='utf8').read().split('=', 1)[1].strip().rstrip(';'))
for x in (sys.argv[1:] or SLICE):
    w, i, st = SLICE[x]; mp3, info = cut(x, w, i, st)
    open(f'{ROOT}/audio/{fn("snd:" + x)}', 'wb').write(mp3); mf['snd:' + x] = fn('snd:' + x); print(x, info, len(mp3))
open(mp, 'w', encoding='utf8').write('window.AUDIO_MANIFEST = ' + json.dumps(mf, ensure_ascii=False) + ';\n')
