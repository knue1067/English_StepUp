#!/usr/bin/env python3
"""Validate unit JSON files against SCHEMA.md. Usage: python3 validate.py data/L01.json [...]"""
import json, sys

TYPES = {"mc", "listen_mc", "build", "listen_build", "match", "fill", "dialog", "speak", "type", "read"}


def check_ex(ex, where, errs):
    t = ex.get("type")
    if t not in TYPES:
        errs.append(f"{where}: bad type {t!r}"); return
    def need(*keys):
        for k in keys:
            if k not in ex or ex[k] in (None, "", []):
                errs.append(f"{where} ({t}): missing {k}")
    if t in ("mc", "listen_mc", "fill", "dialog", "read"):
        need("choices")
        ch = ex.get("choices") or []
        a = ex.get("answer")
        if not isinstance(a, int) or not (0 <= a < len(ch)):
            errs.append(f"{where} ({t}): answer index {a!r} out of range")
        if len(set(ch)) != len(ch):
            errs.append(f"{where} ({t}): duplicate choices")
        if not 2 <= len(ch) <= 5:
            errs.append(f"{where} ({t}): {len(ch)} choices")
    if t == "listen_mc": need("audio")
    if t == "fill":
        need("sentence")
        if ex.get("sentence", "").count("___") != 1:
            errs.append(f"{where} (fill): sentence must contain exactly one ___")
    if t == "dialog":
        need("lines")
        if sum(1 for l in ex.get("lines", []) if l.get("text") == "?") != 1:
            errs.append(f"{where} (dialog): exactly one line must have text '?'")
    if t == "read": need("passage", "question")
    if t in ("build", "listen_build"):
        need("answer")
        if not isinstance(ex.get("answer"), str):
            errs.append(f"{where} ({t}): answer must be a string")
        if t == "build": need("ko")
        if t == "listen_build": need("audio")
        toks = set(str(ex.get("answer", "")).split())
        for d in ex.get("distractors", []):
            if d in toks:
                errs.append(f"{where} ({t}): distractor {d!r} also in answer")
    if t == "match":
        p = ex.get("pairs") or []
        if not 3 <= len(p) <= 6 or any(len(x) != 2 for x in p):
            errs.append(f"{where} (match): need 3-6 pairs of 2")
        if len({x[0] for x in p}) != len(p) or len({x[1] for x in p}) != len(p):
            errs.append(f"{where} (match): duplicate sides")
    if t == "speak": need("text")
    if t == "type":
        need("ko", "answers")
        if not isinstance(ex.get("answers"), list):
            errs.append(f"{where} (type): answers must be a list")


def main(paths):
    total = 0
    bad = False
    for path in paths:
        errs = []
        d = json.load(open(path))
        uid = d.get("id", path)
        if uid.startswith("L"):
            for k in ("title", "emoji", "functions", "forms", "newWords", "keyWords", "goals", "periods", "dialogs", "reading", "writing"):
                if k not in d: errs.append(f"{uid}: missing {k}")
            ps = d.get("periods", [])
            g = d.get("grade", 5)
            need = 6 if g in (5, 6) else (5 if (g == 3 and d.get("no") == 1) else 4)
            if len(ps) != need: errs.append(f"{uid}: {len(ps)} periods (need {need} for grade {g})")
            if g != 5:
                if "grade" not in d: errs.append(f"{uid}: missing grade")
                for p in ps:
                    if p.get("icon") not in ("chat", "mic", "read", "book", "pencil", "trophy", "abc"): errs.append(f"{uid} p{p.get('n')}: bad/missing icon")
                    if not p.get("kind"): errs.append(f"{uid} p{p.get('n')}: missing kind")
            import re as _re
            for p in ps:
                for key in ("exercises", "exercises2", "exercises3"):
                    for i, ex in enumerate(p.get(key, [])):
                        txt = " ".join(str(ex.get(k, "")) for k in ("prompt", "question"))
                        if _re.search(r"Fun Talk|Talk Like This|Story Time|Let'?s Read|Chant|Song|노래|찬트|만화 ?영화|동영상", txt):
                            errs.append(f"{uid} p{p.get('n')} {key}[{i}]: prompt mentions a textbook section — must be self-contained")
            for p in ps:
                for k in ("n", "title", "studyPoint", "objectives", "flow", "keyExpressions", "exercises"):
                    if k not in p: errs.append(f"{uid} p{p.get('n')}: missing {k}")
                seen = set()
                for key in ("exercises", "exercises2", "exercises3"):
                    exs = p.get(key, [])
                    if len(exs) < 8: errs.append(f"{uid} p{p.get('n')}: {key} has only {len(exs)} exercises")
                    for i, ex in enumerate(exs):
                        check_ex(ex, f"{uid} p{p.get('n')} {key}[{i}]", errs); total += 1
                        sig = json.dumps({k: ex.get(k) for k in ("type", "prompt", "answer", "choices", "audio", "text", "sentence", "question", "passage", "ko", "answers", "pairs", "lines", "emoji")}, sort_keys=True, ensure_ascii=False)
                        if sig in seen: errs.append(f"{uid} p{p.get('n')} {key}[{i}]: duplicate of an exercise in another stage")
                        seen.add(sig)

        else:
            for key in ("exercises", "exercises2", "exercises3"):
                exs = d.get(key, [])
                if len(exs) < 10: errs.append(f"{uid}: {key} has only {len(exs)} exercises")
                for i, ex in enumerate(exs):
                    check_ex(ex, f"{uid} {key}[{i}]", errs); total += 1
        if errs:
            bad = True
            print(f"✗ {path}: {len(errs)} problems"); [print("   ", e) for e in errs]
        else:
            print(f"✓ {path}")
    print("total exercises:", total)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
