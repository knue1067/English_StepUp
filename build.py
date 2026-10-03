#!/usr/bin/env python3
"""Inline every grade's unit data (data/g3 … data/g6) into app.html -> index.html"""
import json, glob, os, sys
here = os.path.dirname(os.path.abspath(__file__))
grades, summary = {}, []
for gdir in sorted(glob.glob(os.path.join(here, 'data', 'g*'))):
    g = os.path.basename(gdir)[1:]
    units, reviews = [], []
    for f in sorted(glob.glob(os.path.join(gdir, '*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        (reviews if d['id'].startswith('R') else units).append(d)
    if units:
        grades[g] = {'units': units, 'reviews': reviews}
        summary.append(f'{g}학년 {len(units)}단원/{len(reviews)}리뷰')
data = json.dumps({'grades': grades}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
src = open(os.path.join(here, 'app.html'), encoding='utf-8').read()
marker = '/*__DATA__*/{"grades":{}}'
assert marker in src
body = src.replace(marker, data)
# standalone file (double-click to open) gets its own document skeleton
head = '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
open(os.path.join(here, 'index.html'), 'w', encoding='utf-8').write(head + body + '\n</html>\n')
# bare version for publishing (publisher adds the skeleton)
if len(sys.argv) > 1:
    open(sys.argv[1], 'w', encoding='utf-8').write(body)
print('built index.html:', ', '.join(summary), f'{os.path.getsize(os.path.join(here, "index.html"))//1024} KB')
