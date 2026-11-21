"""Pull the latest successful run of each Apify task and append it to data/raw/*.json.

Needs APIFY_TOKEN plus one task ID per source (see config/sources.json -> env_task_id),
set as environment variables or GitHub Actions secrets. Sources without a task ID are
skipped; with no token at all the build falls back to the demo data.
"""
import json
import os
import pathlib
import urllib.request
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "sources.json").read_text())
RAW = ROOT / "data" / "raw"
API = "https://api.apify.com/v2/actor-tasks/{task}/runs/last/dataset/items?status=SUCCEEDED&clean=true&format=json"


def g(d, *keys, default=""):
    for k in keys:
        cur = d
        for part in k.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur not in (None, ""):
            return cur
    return default


def norm_social(name, item, run):
    src = {"reddit": "Reddit", "x": "X", "linkedin": "LinkedIn"}[name.replace("pains_", "")]
    return [{"run_date": run, "source": src,
             "title": g(item, "title", "postTitle"), "text": g(item, "body", "text", "content"),
             "url": g(item, "url", "postUrl", "linkedinUrl"),
             "posted": str(g(item, "createdAt", "commentCreatedAt", "postedAt.date", "postedAt"))[:10],
             "author": g(item, "author.username", "author.name", "subredditName", "communityName"),
             "query": g(item, "searchTerm", "query")}]


def norm_google(item, run):
    return [{"run_date": run, "source": "Google", "title": r.get("title", ""), "text": r.get("description", ""),
             "url": r.get("url", ""), "posted": str(r.get("date", ""))[:10], "author": "",
             "query": g(item, "searchQuery.term")} for r in item.get("organicResults", [])]


def norm_aio(item, run, brand_re, own_domain):
    import re
    aio = json.dumps(item.get("aiOverview") or "")
    pos = next((i + 1 for i, r in enumerate(item.get("organicResults", [])) if own_domain in r.get("url", "")), "")
    return [{"run_date": run, "platform": "Google AI Overview", "prompt": g(item, "searchQuery.term"),
             "in_answer": "no answer" if not item.get("aiOverview") else "yes" if re.search(brand_re, aio, re.I) else "no",
             "organic_pos": pos, "snippet": ""}]


def main():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN not set: skipping fetch, build uses demo data.")
        return
    RAW.mkdir(parents=True, exist_ok=True)
    run = date.today().isoformat()
    buckets = {"mentions": [], "pains": [], "ai": []}
    for name, src in CFG["sources"].items():
        task = os.environ.get(src["env_task_id"])
        if not task:
            continue
        req = urllib.request.Request(API.format(task=task), headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=180) as r:
            items = json.load(r)
        for it in items:
            if name == "ai_aio":
                buckets["ai"] += norm_aio(it, run, CFG["brand_regex"], CFG["own_domain"])
            elif name == "google":
                buckets["mentions"] += norm_google(it, run)
            elif name.startswith("pains_"):
                buckets["pains"] += norm_social(name, it, run)
            else:
                buckets["mentions"] += norm_social(name, it, run)
        print(f"{name}: {len(items)} items")
    for key, rows in buckets.items():
        f = RAW / f"{key}.json"
        old = json.loads(f.read_text()) if f.exists() else []
        old = [r for r in old if r["run_date"] != run] + rows  # rerun on the same day replaces that day
        f.write_text(json.dumps(old, ensure_ascii=False))


if __name__ == "__main__":
    main()
