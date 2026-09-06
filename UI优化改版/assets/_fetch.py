"""Image priority fetcher v2 - all path segments URL-encoded."""
import urllib.request
import urllib.parse
import os
import socket
import json

socket.setdefaulttimeout(10)

PINYIN = ['feiyu', 'zhaoyebai', 'yunqi', 'lansheng', 'zhaohun',
          'wenling', 'buyuege', 'shishitongtang']

CN = {
    'feiyu': '\u7fe0\u7389',
    'zhaoyebai': '\u7167\u591c\u767d',
    'yunqi': '\u4e91\u8d77',
    'lansheng': '\u6f9c\u751f',
    'zhaohun': '\u62db\u9b42',
    'wenling': '\u95ee\u7075',
    'buyuege': '\u6b65\u6708\u6b4c',
    'shishitongtang': '\u67ff\u67ff\u540c\u5802',
}

TC_CN = {
    'concept': '\u6982\u5ff5\u56fe',
    'design':  '\u8bbe\u8ba1\u56fe',
    'fabric':  '\u5e03\u6599\u56fe',
    'garment': '\u6210\u8863\u56fe',
    'model':   '\u6a21\u7279\u56fe',
}

# Per brand: full priority chain (concept first)
CHAIN = [
    ('concept', '01'),
    ('design',  '01'),
    ('design',  '02'),
    ('fabric',  '01'),
    ('garment', '01'),
    ('model',   '01'),
]

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA,
           'Accept': 'image/avif,image/webp,*/*',
           'Referer': 'https://products.nanyiqiutang.cn/'}

OUT = '.'
existing = set(os.listdir(OUT))
manifest = {}
ok = fail = skip = 0

for pn in PINYIN:
    cn = CN[pn]
    manifest[pn] = []
    for t, idx in CHAIN:
        tc = TC_CN[t]
        fname = f'{pn}-{t}-{idx}.jpg'
        if fname in existing:
            manifest[pn].append({'type': t, 'cn': tc, 'idx': idx, 'file': fname, 'status': 'skip'})
            skip += 1
            continue
        # all segments URL-encoded
        url = (f'https://products.nanyiqiutang.cn/static/images/'
               f'{urllib.parse.quote(cn)}/'
               f'{urllib.parse.quote(cn)}-{urllib.parse.quote(tc)}-{idx}.jpg'
               f'?v=20260805-1')
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()
                if len(data) > 1500:
                    with open(os.path.join(OUT, fname), 'wb') as f:
                        f.write(data)
                    manifest[pn].append({'type': t, 'cn': tc, 'idx': idx, 'file': fname,
                                          'status': 'ok', 'bytes': len(data)})
                    ok += 1
                    print(f'  + {fname:34s} {len(data):>7} B')
                else:
                    manifest[pn].append({'type': t, 'cn': tc, 'idx': idx, 'file': fname, 'status': 'tiny'})
                    fail += 1
                    print(f'  . {fname:34s} too-small')
        except Exception as e:
            manifest[pn].append({'type': t, 'cn': tc, 'idx': idx, 'file': fname,
                                 'status': 'miss', 'err': type(e).__name__})

with open('_image_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f'\nok={ok}  fail/tiny={fail}  skip={skip}')
