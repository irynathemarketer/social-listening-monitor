# Social Listening Monitor

**A lightweight social listening tool for a few dollars a month.** Apify collects brand mentions, market pain threads and AI answers every week. Python cleans and tags them. A static page on GitHub Pages shows what changed and what needs a reaction.

**[Live demo →](https://paulythemarketer-source.github.io/social-listening-monitor/)** (fictional SaaS brand "Acme Cloud", generated data)

## The problem

Paid listening tools cost $100+ a month and still drown you in noise: homonyms, job ads, your own posts. For a B2B brand with a few dozen mentions a week, you need something smaller and sharper:

- Who wrote about us this week, and was it negative?
- What is the market complaining about, and which competitors keep coming up?
- Do ChatGPT, Gemini and Google AI Overview name us, or someone else?

## What the dashboard shows

| Block | Question it answers |
|---|---|
| Numbers | Mentions, third-party share, review score, negative share and AI visibility, each with its trend |
| Signals | Negative mentions, spam, unanswered reviews, review spikes, drops in AI share, pain topics that are growing |
| Narratives | What people talk about when they mention the brand, and how negative each topic is |
| Where | Mentions by platform and industry, with own posts, listings and spam tagged |
| Reviews | Monthly volume, negative spikes (mean + 2σ), negative vs positive themes |
| Market pains | Brand-free threads by pain cluster and platform: this is where demand sits |
| Competitors | Who gets named in complaints, and what they get blamed for |
| AI answers | Share of prompts where AI names the brand, by platform |

## How it works

```
Apify tasks (weekly)  →  scripts/fetch.py  →  data/raw/*.json  (history)
                                               ↓
config/sources.json   →  scripts/build.py  →  docs/data.json
                                               ↓
                                       docs/index.html  (GitHub Pages)
```

- **Collection:** public Apify actors `apify/google-search-scraper`, `harshmaur/reddit-scraper`, `xquik/x-tweet-scraper`, `harvestapi/linkedin-post-search`. AI Overview checks use the Google Search scraper on a fixed prompt list.
- **Cleaning and tagging:** plain keyword rules in `config/sources.json`: brand pattern, noise, own posts, spam, listings, negative words, industries, narratives, pain clusters, competitors. They are rules on purpose, so every tag can be explained.
- **Dashboard:** one static HTML file with d3. No backend, no build step.
- **Schedule:** a GitHub Action runs weekly, pulls the last Apify runs, rebuilds the data and commits it.

## Cost

Apify charges per result, so the bill depends on how many queries and sources you run. A weekly run of four brand sources, two pain sources and a short AI prompt list fits within the Apify free plan's monthly credit. Set a spending cap per task. GitHub Actions and Pages are free for public repos.

## Use it for your brand

1. Fork this repo and turn on **Settings → Pages → Deploy from branch → `main` / `docs`**.
2. Edit `config/sources.json`: brand name and regex, own domain, competitors, rules.
3. In Apify, create one task per source with your queries (templates are in `query_templates`).
4. Add **Settings → Secrets → Actions**: `APIFY_TOKEN` and the task IDs (`TASK_GOOGLE`, `TASK_REDDIT`, …).
5. Run **Actions → Weekly collection → Run workflow**. The page switches from demo to live data.

Run it locally:

```bash
python scripts/make_demo.py   # regenerate demo data
python scripts/build.py       # build docs/data.json
cd docs && python -m http.server
```

## Notes

- The demo brand, competitors, people and texts are invented. URLs use the reserved `.example` domain.
- Rule-based tagging is a deliberate choice: it is cheap, repeatable and easy to audit. Swap in an LLM classifier if you need nuance.

---

Built by **Polina Lebedev**, product marketer: B2B go-to-market, GEO and AI visibility.
