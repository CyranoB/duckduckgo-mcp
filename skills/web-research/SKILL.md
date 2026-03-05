---
name: web-research
license: MIT
metadata:
  author: CyranoB
  version: "1.0.0"
description: >
  Deep web research skill that searches the web and fetches full page content to produce
  comprehensive, well-sourced research reports. Use this skill whenever the user asks to
  research a topic, investigate a question, do a deep dive, compare products or services,
  look something up online, find information about a product/company/technology, or gather
  current information from the web. Trigger on phrases like "can you find out about X",
  "look up X", "what do you know about X (current/recent)", "tell me about X",
  "research X for me", "help me understand X", "what are people saying about X",
  "I'm choosing between X and Y", or "search the web for X" when current web info would
  be valuable. Also trigger when the user needs recent news, pricing, reviews, or
  real-world adoption data that may have changed since training. Don't trigger for purely
  conceptual questions that Claude can answer from training data without needing live web
  sources — unless the user explicitly asks to search the web.
---

# Web Research

This skill guides you through a structured deep research workflow: multi-angle search,
selective full-page fetching, and synthesis into a polished, cited report.

## Tools available

**Search** — run Python with the `ddgs` library:
```python
from ddgs import DDGS
results = DDGS().text(query="your query", max_results=8)
for r in results:
    print(r["title"], r["href"], r["body"])
```
If `ddgs` isn't installed: `pip install ddgs`

**Fetch** — call Jina Reader directly to get a URL as clean markdown:
```bash
curl -s "https://r.jina.ai/https://example.com"
```
Or in Python:
```python
import requests
content = requests.get(f"https://r.jina.ai/{url}").text
```
No API key needed.

If an MCP tool called `mcp__duckduckgo__search` or `mcp__duckduckgo__jina_fetch` is
available in the session, prefer those over the above — they're faster and already wired in.

---

## Research workflow

### Step 1 — Understand the research question

Before searching, take a moment to understand what's actually being asked:
- What's the core question or goal?
- What kind of information would fully answer it? (facts, comparisons, recent news, how-tos, etc.)
- Are there multiple angles worth exploring?

### Step 2 — Multi-angle search strategy

Don't search just once. Run 2–3 searches with different query framings to get broader coverage.
Think about:
- A direct/obvious query ("Python async best practices 2024")
- A more specific angle ("asyncio pitfalls production")
- An alternative framing ("FastAPI async vs sync performance comparison")

Run all searches, collect results. Don't fetch URLs yet — evaluate snippets first.

### Step 3 — Select URLs to fetch

From all the search results, pick the 3–5 most promising URLs based on:
- **Relevance**: does the snippet suggest genuine depth on the topic?
- **Source quality**: authoritative sources, docs, reputable publications over SEO filler
- **Diversity**: don't pick 5 URLs from the same site — spread across sources
- **Recency**: prefer recent sources for fast-moving topics

Briefly explain your URL selection to the user before fetching — this builds trust and
lets them redirect you if you've chosen poorly.

### Step 4 — Fetch full content

Fetch each selected URL using the Jina Reader method above. Use markdown format (default).
If a fetch fails, skip that URL and note it in your sources section.

For very long pages, focus on the most relevant sections rather than including everything.

### Step 5 — Synthesize the report

Write a structured report using the format below. The goal is a document the user can
actually use — not a stream of consciousness, not a list of quotes.

---

## Output format — adaptive

Scale the report to match the question. Not every question needs a 5-section report.

### Quick answer (simple factual question, single-topic lookup)
When the user just needs a fact, a date, a comparison, or a short answer:

```
## [Answer title]
Direct answer in 2–4 sentences, with the key fact front and center.

**Sources:** [Title](url), [Title](url)
```

### Standard report (most research questions)
```
# [Research title]

## Summary
2–4 sentence TL;DR that answers the core question directly.

## Key findings
- Bullet points of the most important, concrete things you learned
- Each bullet should stand alone — avoid "according to source X, ..."
- Include numbers, dates, specifics where available

## Sources
1. [Title](url) — one line describing what this source contributed
```

### Deep dive (complex, multi-faceted, or strategic questions)
```
# [Research title]

## Summary
2–4 sentence TL;DR that answers the core question directly.

## Key findings
- Concrete bullet points with numbers, dates, specifics

## [Topic sections — 2–4 sections, named for what they cover]
Prose paragraphs going deeper on each major aspect.
Cite sources inline as [Source Name](url).

## Limitations & gaps
What you couldn't find, what's uncertain, where the user should dig further.

## Sources
1. [Title](url) — one line describing what this source contributed
2. [Title](url) — ...
```

Use your judgment. The goal is: give the user the right amount of information,
not the maximum amount.

---

## Quality reminders

- **Attribute claims**: when you state something specific you learned from a source, cite it
- **Don't hallucinate**: if you don't find something, say so in Limitations
- **Be concrete**: vague summaries are useless. Dates, numbers, names, versions
- **Stay focused**: it's easy to go wide; keep the report centered on what was actually asked
- **Fresh eyes on the draft**: before presenting, re-read and cut anything repetitive or filler
