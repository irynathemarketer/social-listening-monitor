"""Generate a fictional demo dataset for "Acme Cloud", a made-up B2B SaaS tool.

Everything here is invented: brand, competitors, people, texts, URLs (all *.example).
Writes data/demo/{mentions,pains,reviews,ai}.json in the same normalized shape
that fetch.py produces from real Apify runs.
"""
import json
import pathlib
import random
from datetime import date, timedelta

random.seed(7)
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "demo"
OUT.mkdir(parents=True, exist_ok=True)

RUNS = [date(2026, 10, 13) + timedelta(weeks=i) for i in range(6)]
SOURCES = ["Google", "Reddit", "X", "LinkedIn"]
COMP = ["Competitor A", "Competitor B", "Competitor C", "Competitor D", "Competitor E"]

THIRD = [
    ("Acme Cloud review after six months at our agency", "We run all client reporting in Acme Cloud now. Support is responsive and onboarding was easy.", "pos"),
    ("Is Acme Cloud worth it for a small online store?", "Looking into Acme Cloud for our shop. Anyone using it with e-commerce?", "neu"),
    ("Acme Cloud down again this morning", "Second outage this month, dashboards broken for two hours. Still waiting on a status update.", "neg"),
    ("Acme Cloud vs Competitor B for startups", "Comparing Acme Cloud and Competitor B on pricing and integrations for a seed-stage startup.", "neu"),
    ("Acme Cloud chat integration is great", "The new chat integration from Acme Cloud saves us an hour a day.", "pos"),
    ("Acme Cloud price increase", "Our plan went up 30% with two weeks notice. Considering a cancel and refund.", "neg"),
    ("Using Acme Cloud with 40 students", "Teacher here: set up Acme Cloud for my university course, students picked it up fast.", "pos"),
    ("Top 10 reporting tools for agencies", "List includes Acme Cloud, Competitor A and Competitor C for agencies with many clients.", "neu"),
    ("CSV export in Acme Cloud is limited", "Export only gives CSV, no API for bulk migration. Annoying lock-in.", "neg"),
    ("Acme Cloud support fixed our API issue in a day", "API sync was failing, a manager from Acme Cloud sorted it the next morning. Helpful support.", "pos"),
]
OWN = [
    ("Meet the Acme Cloud team at SaaS Conference", "Booth 12. Come say hi to the Acme Cloud team.", "acmecloud"),
    ("We are hiring: product designer at Acme Cloud", "Join Acme Cloud and build tools for small teams.", "acmecloud"),
    ("My first three months at Acme Cloud", "What I learned in my first three months at Acme Cloud.", "jane-doe-example"),
]
LISTING = [("App directory: tools that integrate with Acme Cloud", "List of apps that integrate with Acme Cloud."),
           ("Acme Cloud partner directory: agencies", "Certified agencies in the Acme Cloud partner directory.")]
NOISE = [("Acme Cloud Bakery opens second location", "Local bakery news, unrelated."),
         ("Hiring now: cashier at Acme Cloud Storage Units", "Apply now for a cashier job.")]
SPAM = [("Free Acme Cloud premium license generator", "Cracked Acme Cloud premium, promo code generator.")]

PAIN_T = [
    ("Looking for a {c} alternative for a 10-person team", "Need an alternative to {c} that does not charge per seat."),
    ("{c} raised prices again", "{c} price increase of 40% on our plan. Too expensive now."),
    ("{c} outage again?", "{c} has been down for an hour, third outage this month. Broken dashboards."),
    ("Any tool that integrates with our CRM?", "{c} has no API or plugin for our CRM."),
    ("{c} support never replies", "Opened a ticket with {c} support a week ago, no reply."),
    ("How to export everything out of {c}?", "Trying to migrate off {c}, export is CSV only. Feels like lock-in."),
]
PROMPTS = ["best reporting tool for marketing agencies", "client dashboard software for small agencies", "Competitor A alternatives",
           "Competitor B vs Competitor C", "best analytics tool for online stores", "reporting tool with chat integration",
           "cheapest team dashboard tool", "dashboard tool for university courses", "how to automate client reports",
           "white-label reporting for agencies", "KPI dashboard for startups", "tool to combine web analytics and ads data",
           "self-serve BI for small teams", "free BI tool alternatives", "client reporting automation"]


def url(src, i):
    host = {"Google": "blog.example", "Reddit": "reddit.example/r/saas", "X": "x.example/status", "LinkedIn": "linkedin.example/posts"}[src]
    return f"https://{host}/{i}"


def rand_day(run, back=7):
    return (run - timedelta(days=random.randint(0, back))).isoformat()


mentions, pains, n = [], [], 0
for k, run in enumerate(RUNS):
    for _ in range(random.randint(14, 22) + 2 * k):
        n += 1
        title, text, _ = random.choice(THIRD)
        src = random.choice(SOURCES)
        mentions.append({"run_date": run.isoformat(), "source": src, "title": title, "text": text, "url": url(src, n),
                         "posted": rand_day(run), "author": f"user{random.randint(100, 999)}", "query": "brand"})
    for title, text, author in random.sample(OWN, 2):
        n += 1
        mentions.append({"run_date": run.isoformat(), "source": "LinkedIn", "title": title, "text": text, "url": url("LinkedIn", n),
                         "posted": rand_day(run), "author": author, "query": "brand"})
    for title, text in LISTING + NOISE + (SPAM if k in (2, 5) else []):
        n += 1
        mentions.append({"run_date": run.isoformat(), "source": "Google", "title": title, "text": text, "url": url("Google", n),
                         "posted": rand_day(run), "author": "", "query": "brand"})
    for _ in range(random.randint(25, 40) + 3 * k):
        n += 1
        i = random.randrange(len(PAIN_T))
        t, x = PAIN_T[i]
        # outages cluster around two competitors so the risk chart has a story
        c = random.choices(COMP, weights=[1, 1, 3, 4, 3] if i == 2 else [5, 4, 2, 1, 1])[0]
        src = random.choice(["Reddit", "Reddit", "X", "Google"])
        pains.append({"run_date": run.isoformat(), "source": src, "title": t.format(c=c), "text": x.format(c=c), "url": url(src, n),
                      "posted": rand_day(run), "author": "", "query": "pains"})

REV_POS = [("Easy onboarding", "Set up in an afternoon, support helpful."), ("Great integrations", "Integration with our chat and CRM works well, pricing fair."),
           ("Reliable dashboards", "Reports load fast and never break.")]
REV_NEG = [("Outages every week", "Dashboards down again, support slow to reply."), ("Price hike", "Plan price went up with no warning, expensive now."),
           ("Export is a pain", "Cannot export data properly, migration is a nightmare.")]
reviews, d = [], date(2025, 6, 1)
while d <= date(2026, 11, 1):
    spike = d.strftime("%Y-%m") in ("2025-12", "2026-07")
    for _ in range(random.randint(3, 9)):
        neg = random.random() < (0.75 if spike else 0.25)
        title, text = random.choice(REV_NEG if neg else REV_POS)
        rating = random.choice([1, 2]) if neg else random.choice([4, 5, 5, 3])
        day = min(d + timedelta(days=random.randint(0, 27)), date(2026, 11, 16))
        reviews.append({"date": day.isoformat(), "rating": rating, "title": title, "text": text,
                        "country": random.choice(["US", "GB", "DE", "FR", "CA", "AU"]), "reply": "yes" if random.random() < 0.6 else "no",
                        "url": f"https://reviews.example/acmecloud/{len(reviews)}"})
    d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)

ai = []
for k, run in enumerate(RUNS):
    for p in PROMPTS:
        r = random.random()
        ans = "no answer" if r < 0.06 else "yes" if r < 0.12 + 0.03 * k else "no"
        ai.append({"run_date": run.isoformat(), "platform": "Google AI Overview", "prompt": p, "in_answer": ans,
                   "organic_pos": random.choice(["", "", 1, 3, 4, 6, 9]), "snippet": "Acme Cloud offers client dashboards for agencies." if ans == "yes" else ""})
    if k in (1, 5):
        for p in PROMPTS[:5]:
            ai.append({"run_date": run.isoformat(), "platform": "Gemini", "prompt": p, "in_answer": "yes" if random.random() < 0.3 else "no",
                       "organic_pos": "", "snippet": ""})

for name, rows in [("mentions", mentions), ("pains", pains), ("reviews", reviews), ("ai", ai)]:
    (OUT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0))
    print(name, len(rows))
