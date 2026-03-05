---
name: news-monitor
license: MIT
metadata:
  author: CyranoB
  version: "1.1.0"
description: >
  Search for recent news and developments on a topic, organize them chronologically,
  and deliver a concise briefing. Use this skill when the user wants to catch up on
  recent events, news, or developments around a topic. Trigger on phrases like "what's
  new with X", "recent news about X", "any updates on X", "what happened with X lately",
  "catch me up on X", "news roundup for X", "what did I miss about X", "latest
  developments in X", or "has anything changed with X recently". Also trigger when the
  user mentions a time frame like "this week", "this month", "since January", or "in
  the last few days" combined with wanting information. Don't trigger for general
  research, product comparisons, or fact-checking — only when recency is the point.
---

# News Monitor

This skill finds recent news and developments on a topic and delivers a chronological
briefing. The focus is on *what's new* — not a general overview.

## Design principle: search results first, fetch sparingly

The news search tool already returns titles, snippets, dates, and sources for each
result. That's enough to build most of the briefing without fetching any pages. Only
fetch a page when a snippet is too vague to understand what actually happened and you
need the full article to write a useful summary. Most of the time, 0–2 fetches is
plenty. Never fetch more than 3 pages.

## Tools available

**News search** — the primary tool. Returns results sorted by date with timestamps
and source outlets.

If `mcp__duckduckgo__duckduckgo_news_search` is available, prefer it:
```
mcp__duckduckgo__duckduckgo_news_search(query="your query", max_results=10)
```
Each result includes `title`, `url`, `snippet`, `date`, and `source`.

Without MCP, use the `ddgs` library directly:
```python
from ddgs import DDGS
results = DDGS().news(query="your query", max_results=10)
for r in results:
    print(r["date"], r["title"], r["url"], r["source"])
```
If `ddgs` isn't installed: `pip install ddgs`

**General search** — use `mcp__duckduckgo__search` or `DDGS().text()` only if news
search returns too few results.

**Fetch** — use `mcp__duckduckgo__jina_fetch` or `curl -s "https://r.jina.ai/URL"`
only when a snippet is too vague to summarize the event. Cap fetches with
`max_length=3000` to avoid pulling giant pages.

---

## News monitoring workflow

### Step 1 — Determine scope

Before searching, clarify:
- **Topic**: what exactly are we monitoring?
- **Time frame**: did the user specify "this week", "last month", "since X"? If not,
  default to the last 2–4 weeks.
- **Angle**: are they interested in everything, or a specific aspect (e.g., "funding
  news about X", "regulatory updates on Y")?

### Step 2 — Search

Run 1–2 news searches with different angles to get good coverage:
- `"[topic]"` as the base query
- A second query with a more specific angle if relevant (e.g., "[topic] announcement",
  "[topic] policy", "[topic] release")

Include the current year in queries to bias toward recent results.

### Step 3 — Deduplicate and filter

From the combined news results:
- Group articles about the same event (multiple outlets covering the same story)
- Pick the best source for each event (prefer the one with the most informative snippet)
- Discard anything outside the relevant time frame
- Discard duplicates or near-duplicates
- Aim for 3–7 distinct events

### Step 4 — Selective fetch (only if needed)

Look at your filtered results. For each event, ask: "Can I write a useful 2–4 sentence
summary from the title + snippet alone?" If yes, don't fetch. If the snippet is cryptic
or you need key details (numbers, names, outcomes), fetch that one page with
`max_length=3000`.

### Step 5 — Deliver the briefing

Organize chronologically (most recent first) and present as a news briefing.

---

## Output format

```
# [Topic] — News Briefing

**Period**: [time frame covered]
**Last updated**: [today's date]

## Headlines
- [One-line summary of event 1] — [date]
- [One-line summary of event 2] — [date]
- [One-line summary of event 3] — [date]

## Details

### [Event 1 title] — [date]
[2–4 sentences: what happened, why it matters, what's next]
Source: [Title](url)

### [Event 2 title] — [date]
[2–4 sentences]
Source: [Title](url)

### [Event 3 title] — [date]
[2–4 sentences]
Source: [Title](url)

## What to watch
[1–2 sentences about upcoming events, expected announcements, or unresolved threads
that the user might want to follow up on]
```

Keep it tight. The user wants to catch up quickly, not read essays. If there's genuinely
no recent news, say so — "No significant developments found in [time frame]" is a valid
and useful answer.
