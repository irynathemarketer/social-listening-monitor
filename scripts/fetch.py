"""Collect this week's data and append it to data/raw/*.json.

- Apify: the latest successful run of each task (APIFY_TOKEN + one task ID per source,
  see config/sources.json -> env_task_id). Google, Reddit, X, LinkedIn, Google AI Overview, Gemini.
- ChatGPT: asks the prompts in config/sources.json -> ai_prompts through the OpenAI API
  with web search (OPENAI_API_KEY, optional OPENAI_MODEL).

Everything is optional: a source without its secret is skipped, and with nothing set
the build falls back to the demo data.
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


def norm_gemini(item, run, brand_re, own_domain):
    import re
    if not item.get("text"):
        return [{"run_date": run, "platform": "Gemini", "prompt": item.get("query", ""), "in_answer": "no answer", "organic_pos": "", "snippet": ""}]
    cited = [s.get("url", "") for s in item.get("sources", [])]
    named = re.search(brand_re, item["text"], re.I) or any(own_domain in u for u in cited)
    return [{"run_date": run, "platform": "Gemini", "prompt": item.get("query", ""), "in_answer": "yes" if named else "no",
             "organic_pos": "", "snippet": ""}]


def ask_chatgpt(prompt, run, key, model, brand_re, own_domain):
    """One prompt through the OpenAI Responses API with the web_search tool."""
    import re
    body = {"model": model, "tools": [{"type": "web_search"}], "input": prompt}
    req = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    text, urls = "", []
    for out in resp.get("output", []):
        for part in out.get("content", []) or []:
            if part.get("type") == "output_text":
                text += part.get("text", "")
                urls += [a.get("url", "") for a in part.get("annotations", []) if a.get("type") == "url_citation"]
    if not text:
        return {"run_date": run, "platform": "ChatGPT", "prompt": prompt, "in_answer": "no answer", "organic_pos": "", "snippet": ""}
    named = re.search(brand_re, text, re.I) or any(own_domain in u for u in urls)
    pos = next((i + 1 for i, u in enumerate(urls) if own_domain in u), "")
    return {"run_date": run, "platform": "ChatGPT", "prompt": prompt, "in_answer": "yes" if named else "no", "organic_pos": pos, "snippet": ""}


def main():
    token, okey = os.environ.get("APIFY_TOKEN"), os.environ.get("OPENAI_API_KEY")
    if not token and not okey:
        print("No APIFY_TOKEN or OPENAI_API_KEY: skipping fetch, build uses demo data.")
        return
    RAW.mkdir(parents=True, exist_ok=True)
    run = date.today().isoformat()
    buckets = {"mentions": [], "pains": [], "ai": []}
    if okey:
        model = os.environ.get("OPENAI_MODEL") or "gpt-5.5"
        for p in CFG.get("ai_prompts", []):
            buckets["ai"].append(ask_chatgpt(p, run, okey, model, CFG["brand_regex"], CFG["own_domain"]))
        print(f"chatgpt: {len(CFG.get('ai_prompts', []))} prompts")
    for name, src in (CFG["sources"].items() if token else []):
        task = os.environ.get(src["env_task_id"])
        if not task:
            continue
        req = urllib.request.Request(API.format(task=task), headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=180) as r:
            items = json.load(r)
        for it in items:
            if name == "ai_aio":
                buckets["ai"] += norm_aio(it, run, CFG["brand_regex"], CFG["own_domain"])
            elif name == "ai_gemini":
                buckets["ai"] += norm_gemini(it, run, CFG["brand_regex"], CFG["own_domain"])
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
