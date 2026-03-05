---
name: competitive-intel
license: MIT
metadata:
  author: CyranoB
  version: "1.0.0"
description: >
  Build a structured comparison of multiple products, services, or tools to help make
  a decision. Produces a comparison matrix with pricing, features, pros/cons, and a
  recommendation. Use this skill when the user wants to compare specific options side
  by side for a purchase or adoption decision. Trigger on phrases like "compare X vs Y",
  "X vs Y vs Z", "which is better X or Y", "help me choose between X and Y",
  "what's the best option for [use case]", "pros and cons of X vs Y", "should I go
  with X or Y", or "I'm deciding between X, Y, and Z for [purpose]". Don't trigger
  for general research about a single topic, fact-checking, or news monitoring —
  only when the user has multiple named options they're evaluating.
---

# Competitive Intel

This skill builds a structured side-by-side comparison of multiple options to support
a decision. The output is a comparison matrix with concrete data, not vague hand-waving.

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

If MCP search/fetch tools are available in the session (e.g., `mcp__web_forager__search`,
`mcp__duckduckgo__search`, or similar), prefer those over the above.

---

## Comparison workflow

### Step 1 — Identify the options and criteria

Before searching, clarify:
- **Options**: which specific products/services/tools are being compared? (2–5 options)
- **Use case**: what is the user trying to do? This determines which criteria matter.
- **Deal-breakers**: are there must-haves or constraints? (budget, platform, team size, etc.)

If the user hasn't specified criteria, infer the most relevant ones from the use case.
Common dimensions: pricing, features, performance, ease of use, ecosystem/integrations,
support, community, documentation.

### Step 2 — Search strategy

Run searches designed to surface comparison data:
- Head-to-head: "[Option A] vs [Option B] [year]"
- Per-option pricing: "[Option A] pricing plans [year]"
- Per-option reviews: "[Option A] review [use case context]"
- If 3+ options: "[category] comparison [year]" to find roundup articles

### Step 3 — Fetch pricing and feature pages

Prioritize fetching:
1. **Official pricing pages** for each option — these have the most accurate, current data
2. **Head-to-head comparison articles** from reputable sources
3. **User reviews or discussions** (Reddit, HN, Trustpilot) for real-world perspective

For each option, try to get at least one official source and one independent source.

### Step 4 — Build the comparison

Organize findings into a structured comparison. For each criterion:
- Use specific numbers, not vague qualifiers ("$29/mo" not "affordable")
- Note what's included vs. what costs extra
- Flag where information couldn't be verified or wasn't found

### Step 5 — Make a recommendation

Based on the evidence and the user's stated use case, provide a clear recommendation.
It's OK to recommend different options for different scenarios — "If X matters most,
go with A; if Y matters most, go with B" is more useful than a forced single pick.

---

## Output format

```
# [Option A] vs [Option B] [vs Option C...]

## TL;DR
[2–3 sentences: the bottom line for this user's specific use case]

## Comparison matrix

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Pricing   | $X/mo    | $Y/mo    | Free     |
| [Key feature 1] | Yes | No | Partial |
| [Key feature 2] | ... | ... | ... |
| ...       | ...      | ...      | ...      |

## Per-option summary

### [Option A]
**Best for**: [one-line use case fit]
**Pros**: [2–4 bullets]
**Cons**: [2–4 bullets]

### [Option B]
**Best for**: [one-line use case fit]
**Pros**: [2–4 bullets]
**Cons**: [2–4 bullets]

## Recommendation
[Clear recommendation tied to the user's use case. Explain the reasoning.
If it depends on factors, lay out the decision tree.]

## Sources
1. [Title](url) — [what data came from this source]
```

The comparison matrix is the centerpiece — make it scannable and data-rich. Use actual
numbers, plan names, and specifics. "Good support" means nothing; "24/7 live chat on
Pro plan, email-only on Free" means everything.
