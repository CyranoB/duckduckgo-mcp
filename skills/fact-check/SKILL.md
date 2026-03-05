---
name: fact-check
license: MIT
metadata:
  author: CyranoB
  version: "1.0.0"
description: >
  Verify claims and statements by searching for supporting and contradicting evidence,
  then deliver a clear verdict with confidence level and sources. Use this skill when
  the user asks to fact-check something, verify a claim, check if something is true,
  or questions the accuracy of a statement. Trigger on phrases like "is it true that X",
  "fact check this", "verify this claim", "is X really Y", "I heard that X — is that
  accurate?", "can you confirm that X", "someone told me X", or "this article says X,
  is that right?". Don't trigger for general research questions or product comparisons —
  only when the user has a specific claim they want verified.
---

# Fact Check

This skill verifies a specific claim by searching for evidence on both sides,
evaluating source quality, and delivering a clear verdict.

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

## Fact-checking workflow

### Step 1 — Extract the claim

Identify the specific, verifiable claim. If the user's statement is vague or compound,
break it into distinct claims and address each one. Restate the claim back to the user
so they can confirm you understood it correctly.

Bad: "AI is taking over" (too vague to verify)
Good: "OpenAI's revenue exceeded $3 billion in 2024" (specific, verifiable)

If the claim is inherently subjective or a matter of opinion ("React is better than Vue"),
say so upfront — opinion claims can't be fact-checked, only contextualized.

### Step 2 — Search for supporting evidence

Search for sources that would confirm the claim. Frame queries to find the claim stated
as fact:
- Direct query: the claim itself in quotes or close paraphrase
- Source-seeking: "[subject] official statement [topic]"
- Data query: "[subject] statistics [specific metric]"

### Step 3 — Search for contradicting evidence

Now actively look for the other side. This is the step most people skip, and it's the
most important one. Frame queries to find disagreement:
- "[claim subject] debunked" or "[claim subject] false"
- "[claim subject] criticism" or "[claim subject] controversy"
- Alternative framing that would surface opposing data

### Step 4 — Fetch key sources

From both searches, pick the 2–4 most authoritative sources to fetch in full.
Prioritize:
- Primary sources (official announcements, papers, data sets) over commentary
- Established publications over random blogs
- Sources with specific data points over vague assertions

### Step 5 — Evaluate and deliver verdict

Weigh the evidence. Consider:
- **Source authority**: who published this? Do they have expertise or a conflict of interest?
- **Specificity**: does the evidence address the exact claim, or something adjacent?
- **Recency**: is the evidence current enough to be relevant?
- **Consensus**: do multiple independent sources agree?

---

## Output format

```
## Claim
> [The claim being checked, stated clearly]

## Verdict: [CONFIRMED / LIKELY TRUE / UNVERIFIED / DISPUTED / FALSE]

[2–3 sentence explanation of the verdict — why this rating, what the key evidence is]

## Evidence supporting the claim
- [Specific finding with source citation] — [Source Name](url)
- ...

## Evidence against the claim
- [Specific finding with source citation] — [Source Name](url)
- ...
(If no contradicting evidence was found, say so explicitly)

## Caveats
[Anything that limits confidence: old data, limited sources, nuance the binary
verdict doesn't capture]

## Sources
1. [Title](url) — [brief note on what this source is]
```

### Verdict scale

- **CONFIRMED**: Multiple authoritative sources agree; no credible contradiction found
- **LIKELY TRUE**: Good evidence supports it, but with minor gaps or caveats
- **UNVERIFIED**: Couldn't find strong evidence either way
- **DISPUTED**: Credible sources disagree with each other
- **FALSE**: Strong evidence contradicts the claim; supporting sources are weak or absent

Be honest about uncertainty. "Unverified" is a perfectly valid result — it's better than
guessing. If the evidence is mixed, say so and explain why.
