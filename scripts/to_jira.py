"""Turn this week's signals into Jira tasks.

Reads docs/data.json (built by build.py), finds what needs a reaction in the latest
collection, and creates one Jira issue per action. Each issue carries a fingerprint
label, so re-running the script never creates duplicates.

Optional. Skipped unless these are set (env vars or GitHub Actions secrets):
  JIRA_BASE_URL     https://your-team.atlassian.net
  JIRA_EMAIL        the account that owns the API token
  JIRA_API_TOKEN    https://id.atlassian.com/manage-profile/security/api-tokens
  JIRA_PROJECT_KEY  e.g. MKT
  JIRA_ISSUE_TYPE   optional, default "Task"

Preview without Jira:  python scripts/to_jira.py --dry-run
"""
import base64
import hashlib
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
LABEL = "social-listening"


def tasks_from(data):
    m, p, rv, ai = data["mentions"], data["pains"], data["reviews"], data["ai"]
    runs = sorted({r["run_date"] for r in m + p})
    if not runs:
        return []
    run, prev = runs[-1], (runs[-2] if len(runs) > 1 else None)
    out = []

    def add(area, summary, why, links=()):
        summary = summary[:240]
        same = next((t for t in out if t["summary"] == summary), None)
        if same:  # the same post seen twice: one task, all links
            same["links"] += [l for l in links if l and l not in same["links"]]
            return
        out.append({"area": area, "summary": summary, "why": why, "links": [l for l in links if l]})

    for r in m:
        if r["run_date"] == run and r["tag"] == "third-party" and r["negative"]:
            add("Brand", f"Respond to negative mention on {r['source']}: {r['title']}", "Negative third-party mention in this week's collection.", [r["url"]])
    spam = [r for r in m if r["run_date"] == run and r["tag"] == "spam"]
    if spam:
        add("Brand", f"Report {len(spam)} spam or impersonation posts", "Posts misuse the brand name.", [r["url"] for r in spam])

    cutoff = (date.fromisoformat(run) - timedelta(days=90)).isoformat()
    no_reply = [r for r in rv if r["negative"] and r.get("reply") != "yes" and cutoff < r["date"] <= run]
    if no_reply:
        add("Support", f"Reply to {len(no_reply)} negative reviews without a response", "Unanswered negative reviews in the last 90 days.", [r["url"] for r in no_reply[:10]])

    if prev:
        now, before = Counter(r["cluster"] for r in p if r["run_date"] == run), Counter(r["cluster"] for r in p if r["run_date"] == prev)
        for k, v in now.items():
            if v >= 3 and before[k] and v >= 1.5 * before[k]:
                add("Content", f"Brief a page on '{k}' ({before[k]} -> {v} threads)", "Market pain topic is growing week over week.")

    def share(d):
        rows = [r for r in ai if r["run_date"] == d and r["platform"] == "Google AI Overview" and r["in_answer"] != "no answer"]
        return 100 * sum(r["in_answer"] == "yes" for r in rows) / len(rows) if rows else None
    s, ps = share(run), share(prev) if prev else None
    if s is not None and ps is not None and s - ps <= -10:
        lost = [r["prompt"] for r in ai if r["run_date"] == run and r["in_answer"] == "no"
                and any(q["prompt"] == r["prompt"] and q["run_date"] == prev and q["in_answer"] == "yes" for q in ai)]
        add("AI search", f"AI Overview share fell {ps:.0f}% -> {s:.0f}%: update pages for lost prompts", "Lost prompts: " + "; ".join(lost[:5]) if lost else "Share of answers naming the brand dropped 10+ pp.")
    return out


def fingerprint(t):
    return "slm-" + hashlib.sha1(t["summary"].encode()).hexdigest()[:10]


def jira(method, path, body=None):
    base = os.environ["JIRA_BASE_URL"].rstrip("/")
    auth = base64.b64encode(f"{os.environ['JIRA_EMAIL']}:{os.environ['JIRA_API_TOKEN']}".encode()).decode()
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def adf(t):
    content = [{"type": "paragraph", "content": [{"type": "text", "text": t["why"]}]}]
    for url in t["links"]:
        content.append({"type": "paragraph", "content": [{"type": "text", "text": url, "marks": [{"type": "link", "attrs": {"href": url}}]}]})
    return {"type": "doc", "version": 1, "content": content}


def main():
    data = json.loads((ROOT / "docs" / "data.json").read_text())
    tasks = tasks_from(data)
    if "--dry-run" in sys.argv or not all(os.environ.get(k) for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY")):
        print(f"{len(tasks)} tasks (dry run, nothing sent to Jira):")
        for t in tasks:
            print(f"- [{t['area']}] {t['summary']}")
        return
    created = 0
    for t in tasks:
        fp = fingerprint(t)
        jql = urllib.parse.quote(f'project = {os.environ["JIRA_PROJECT_KEY"]} AND labels = "{fp}"')
        if jira("GET", f"/rest/api/3/search/jql?jql={jql}&maxResults=1").get("issues"):
            continue
        jira("POST", "/rest/api/3/issue", {"fields": {
            "project": {"key": os.environ["JIRA_PROJECT_KEY"]},
            "issuetype": {"name": os.environ.get("JIRA_ISSUE_TYPE", "Task")},
            "summary": f"[{t['area']}] {t['summary']}",
            "description": adf(t),
            "labels": [LABEL, fp],
        }})
        created += 1
    print(f"Jira: {created} new tasks, {len(tasks) - created} already existed")


if __name__ == "__main__":
    main()
