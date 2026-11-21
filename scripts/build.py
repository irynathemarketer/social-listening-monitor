"""Clean and tag mentions, pain threads and reviews, then write docs/data.json.

Reads data/raw/ (real Apify history) if it has mentions, otherwise data/demo/.
All rules live in config/sources.json, so the same code works for any brand.
"""
import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "sources.json").read_text())
R = lambda p: re.compile(p, re.I)
BRAND, NEG = R(CFG["brand_regex"]), R(CFG["negative"])
N = {k: R(v) for k, v in CFG["noise"].items()}
IND = [(n, R(p)) for n, p in CFG["industries"]]
NARR = [(n, R(p)) for n, p in CFG["narratives"]]
CLUST = [(n, R(p)) for n, p in CFG["pain_clusters"]]
COMP = CFG["competitors"]


def load(folder, name):
    f = folder / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else []


def first(rules, text, default="Other"):
    return next((n for n, p in rules if p.search(text)), default)


def tag_mention(r):
    t = f"{r.get('title', '')} {r.get('text', '')}"
    if not BRAND.search(t) or N["drop"].search(t + " " + r.get("url", "")):
        return None
    if N["own_authors"].search(r.get("author", "")) or N["own_text"].search(t):
        tag = "own"
    elif N["spam"].search(t):
        tag = "spam"
    elif N["listing"].search(t):
        tag = "listing"
    else:
        tag = "third-party"
    return {**r, "tag": tag, "industry": first(IND, t), "negative": bool(NEG.search(t)),
            "themes": [n for n, p in NARR if p.search(t)]}


def tag_pain(r):
    t = f"{r.get('title', '')} {r.get('text', '')}"
    comps = [c for c in COMP if re.search(r"\b" + re.escape(c) + r"\b", t, re.I)]
    return {**r, "cluster": first(CLUST, t), "industry": first(IND, t), "competitors": comps}


def tag_review(r):
    t = f"{r['title']} {r['text']}"
    return {**r, "negative": r["rating"] <= 2, "themes": [n for n, p in NARR if p.search(t)]}


def main():
    raw = ROOT / "data" / "raw"
    folder = raw if load(raw, "mentions") else ROOT / "data" / "demo"
    seen, mentions = set(), []
    for r in load(folder, "mentions"):
        k = (r["run_date"], r["url"])
        if k in seen:
            continue
        seen.add(k)
        m = tag_mention(r)
        if m:
            mentions.append(m)
    out = {
        "brand": CFG["brand"], "competitors": COMP, "mode": "live" if folder == raw else "demo",
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "mentions": mentions,
        "pains": [tag_pain(r) for r in load(folder, "pains")],
        "reviews": [tag_review(r) for r in load(folder, "reviews")],
        "ai": load(folder, "ai"),
    }
    (ROOT / "docs" / "data.json").write_text(json.dumps(out, ensure_ascii=False))
    print(f"{folder.name}: {len(mentions)} mentions, {len(out['pains'])} pain threads, "
          f"{len(out['reviews'])} reviews, {len(out['ai'])} AI checks")


if __name__ == "__main__":
    main()
