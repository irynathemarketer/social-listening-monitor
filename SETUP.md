# Setup guide

Everything here happens in the browser. No terminal, no code. Plan for about an hour the first time.

**What you need:** a GitHub account, an Apify account (the free plan is enough to start), and, if you want tasks in Jira, a Jira Cloud account.

---

## 1. Copy the repo and open the demo

1. At the top of the repo page, click **Fork → Create fork**. You now have your own copy.
2. In your copy, open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, branch `main`, folder `/docs`, then **Save**.
4. Wait a minute and open `https://<your-username>.github.io/social-listening-monitor/`. You'll see the demo with the fictional brand.

## 2. Describe your brand

1. Open `config/sources.json` and click the pencil icon (**Edit this file**).
2. Change:
   - `brand`: your brand name as people write it;
   - `brand_regex`: the same name as a pattern, e.g. `\\byour ?brand\\b` (covers "YourBrand" and "Your Brand");
   - `own_domain`: your site, e.g. `yourbrand.com`;
   - `competitors`: up to 5–10 names;
   - `noise.drop`: words that mean "not us", e.g. a homonym company or job ads;
   - `narratives` and `pain_clusters`: the topics you care about, with the words that signal them.
3. Click **Commit changes**.

Not sure about the rules? Leave the defaults, run one collection, look at what's tagged wrong and adjust.

## 3. Set up Apify

### Get your API token
1. Sign up at apify.com.
2. Open **Settings → API & Integrations** and copy your **Personal API token**. Keep it private: it lets anyone spend your Apify credit.

### Create one task per source
A task is a saved actor with your inputs. Repeat for each source you want:

| Source | Actor to search for in Apify Store | What to put in the input |
|---|---|---|
| Google mentions | `apify/google-search-scraper` | Queries: `"Your Brand" -site:yourbrand.com`, `"Your Brand" review`, `"Your Brand" alternative`. Results per page: 20–30. Country and language of your market. |
| Reddit mentions | `harshmaur/reddit-scraper` | Search term: your brand. Sort: new. Max items: 50. |
| X mentions | `xquik/x-tweet-scraper` | Search term: `"Your Brand"`. Max items: 50. |
| LinkedIn mentions | `harvestapi/linkedin-post-search` | Search query: `"Your Brand"`. Posted: last week. Max posts: 50. |
| Market pains (Reddit, X) | same Reddit and X actors | Brand-free queries about the problems you solve and `<competitor> alternative`. |
| AI answers: Google AI Overview | `apify/google-search-scraper` | 10–30 questions your buyers ask, one per line. Country of your market. |
| AI answers: Gemini | `apify/gemini-search-scraper` | The same buyer questions, one per line. |

For each one:
1. Open the actor in **Apify Store** and click **Create task** (or **Save as a new task** after filling the input).
2. Fill the input as in the table, give the task a clear name (e.g. "Mentions – Google") and **Save**.
3. Click **Start** once and check that the output looks right.
4. Copy the **task ID**: it's in the task's URL (`console.apify.com/actors/tasks/<TASK_ID>`) and on the **API** tab.

### Keep the bill under control
- In the task settings, set a maximum charge per run if the actor offers it.
- In your Apify account settings, set a monthly usage limit.
- Start with fewer queries and lower max items; increase once you see the noise level.

You don't need to schedule tasks in Apify: GitHub starts them weekly (step 5).

### 3b. ChatGPT answers (optional)
ChatGPT has no Apify task here: the weekly job asks your buyer questions through the OpenAI API with web search and checks whether the answer names you or cites your site.

1. Put your buyer questions into `ai_prompts` in `config/sources.json`, one per line in the list.
2. Create an API key at **platform.openai.com → API keys**, and add a small spending limit under **Billing**.
3. Add it as the `OPENAI_API_KEY` secret in step 4.

The API answer is close to what ChatGPT users see but not identical: the app adds personal context and its own settings. Treat it as a trend, not an exact copy.

### 3c. Data from Semrush or other tools (optional)
Already tracking prompts in Semrush AI Visibility, Position Tracking or another tool? You can show them on the same chart.

1. Export the prompts to CSV.
2. Rename the columns to `run_date`, `platform`, `prompt`, `in_answer` (`yes` / `no` / `no answer`) and, if you have it, `organic_pos`. Use a platform name like `ChatGPT (Semrush)` so it stays separate from the API line.
3. Open the `data/import` folder, click **Add file → Upload files**, upload the CSV and commit. The next build adds it. Upload a new file each week, or keep appending to one.

## 4. Add secrets on GitHub

Secrets are passwords and IDs that GitHub stores encrypted for your repo. The weekly job can use them, but nobody can read them: not visitors, not you after saving, and they never appear in the code or on the page.

1. In your repo, open **Settings → Secrets and variables → Actions**.
2. Click **New repository secret** for each line below. **Name** must match exactly; **Secret** is the value.

| Name | Value | Required |
|---|---|---|
| `APIFY_TOKEN` | your Apify API token | yes |
| `TASK_GOOGLE` | task ID for Google mentions | at least one source |
| `TASK_REDDIT` | task ID for Reddit mentions | optional |
| `TASK_X` | task ID for X mentions | optional |
| `TASK_LINKEDIN` | task ID for LinkedIn mentions | optional |
| `TASK_PAINS_REDDIT` | task ID for Reddit pain threads | optional |
| `TASK_PAINS_X` | task ID for X pain threads | optional |
| `TASK_AI_AIO` | task ID for Google AI Overview | optional |
| `TASK_AI_GEMINI` | task ID for Gemini | optional |
| `OPENAI_API_KEY` | OpenAI API key, for ChatGPT answers (step 3b) | optional |
| `OPENAI_MODEL` | OpenAI model name; leave empty for the default | optional |

A source without a task ID is simply skipped.

## 5. Run it

1. Open **Actions → Weekly collection → Run workflow → Run workflow**.
2. Wait 1–3 minutes for a green check.
3. Open your Pages link. The "demo data" badge disappears and your data shows up.

From now on it runs every week on its own. Each run adds a collection to the history, so trends appear after 3–4 weeks.

## 6. Optional: send actions to Jira

Every week, signals become Jira tasks: respond to a negative mention, reply to unanswered reviews, brief a page on a growing pain topic, update pages where AI stopped naming you. Each task links to the sources and is created only once.

1. Create an API token at **id.atlassian.com → Security → Create and manage API tokens → Create API token**. Copy it.
2. Find your project key: it's the prefix of your tickets, e.g. `MKT` in `MKT-123`.
3. Add four more secrets (step 4):

| Name | Value |
|---|---|
| `JIRA_BASE_URL` | `https://your-team.atlassian.net` |
| `JIRA_EMAIL` | the email of the Jira account that created the token |
| `JIRA_API_TOKEN` | the token |
| `JIRA_PROJECT_KEY` | e.g. `MKT` |

4. Run the workflow again. New tasks get the label `social-listening`.

The account must be allowed to create issues in that project. Tasks are created as type "Task"; to use another type, add a secret `JIRA_ISSUE_TYPE` (e.g. `Story`) and the matching line in `.github/workflows/weekly.yml`.

## If something goes wrong

| What you see | What to check |
|---|---|
| Red cross in Actions | Open the run and the failed step; the last lines say why |
| Page still says "demo data" | `APIFY_TOKEN` and at least one mention source (`TASK_GOOGLE`, `TASK_REDDIT`, `TASK_X` or `TASK_LINKEDIN`) are set; the task has a successful run in Apify |
| No ChatGPT line | `OPENAI_API_KEY` is set, the key has credit, and `ai_prompts` in `config/sources.json` is not empty |
| Imported CSV not on the chart | The file is in `data/import/`, ends with `.csv` and has the exact column names |
| A source is empty | The task ran in Apify and returned items; the secret name matches the table exactly |
| Too much noise | Add words to `noise.drop` in `config/sources.json`; make queries more specific |
| No Jira tasks | All four Jira secrets set; the account can create issues; this week actually had signals |
| Page didn't update | **Settings → Pages** still points to `main` / `/docs`; wait a minute and refresh |
