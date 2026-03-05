---
name: tech-radar
license: MIT
metadata:
  author: CyranoB
  version: "1.0.0"
description: >
  Assess a technology's maturity and readiness for adoption. Evaluates community health,
  production usage, ecosystem, known risks, and delivers an Adopt/Trial/Assess/Hold
  recommendation with evidence. Use this skill when the user is evaluating whether to
  adopt a technology, framework, or tool. Trigger on phrases like "should we adopt X",
  "is X production ready", "how mature is X", "is X stable enough for production",
  "what's the risk of using X", "is X ready for prime time", "should I bet on X",
  "is X worth learning", or "how established is X". Also trigger when someone asks about
  a technology's ecosystem, community health, or long-term viability. Don't trigger for
  general research, product comparisons between multiple options, news updates, or
  fact-checking — only when the user wants a maturity/readiness assessment of a
  specific technology.
---

# Tech Radar

This skill evaluates a technology's maturity and delivers an adoption recommendation
using the Adopt / Trial / Assess / Hold framework (inspired by ThoughtWorks Tech Radar).

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

If an MCP tool called `mcp__duckduckgo__search` or `mcp__duckduckgo__jina_fetch` is
available in the session, prefer those over the above.

---

## Assessment workflow

### Step 1 — Understand the context

Before searching, clarify:
- **Technology**: what exactly is being evaluated? (be specific — "React" vs "React Server Components")
- **Context**: what would they use it for? (production app, side project, replacing existing tool)
- **Risk tolerance**: startup moving fast vs enterprise with compliance requirements?

### Step 2 — Multi-dimension search

Search across these dimensions — each one tells a different part of the story:

**Adoption & production use:**
- "[technology] production use cases [year]"
- "[technology] companies using" or "who uses [technology]"

**Ecosystem & community:**
- "[technology] ecosystem libraries plugins"
- "[technology] GitHub stars contributors" or "[technology] community activity"

**Stability & risks:**
- "[technology] known issues limitations"
- "[technology] breaking changes migration"
- "[technology] vs [established alternative]"

**Trajectory:**
- "[technology] roadmap [year]"
- "[technology] adoption trends"

### Step 3 — Fetch key sources

Pick 4–6 URLs across dimensions. Prioritize:
- Official project pages (for roadmap, stability claims)
- Case studies or blog posts from production users
- Community discussions (Reddit, HN) for unfiltered opinions
- Benchmark or comparison articles for performance claims

### Step 4 — Evaluate each dimension

For each dimension, assign a signal strength:

| Dimension | What to look for |
|-----------|-----------------|
| **Adoption** | Named production users, company size, use case diversity |
| **Ecosystem** | Package count, key integrations, tooling quality |
| **Community** | Contributor count, issue response time, activity trends |
| **Stability** | Version history, breaking change frequency, LTS policy |
| **Documentation** | Official docs quality, tutorials, Stack Overflow coverage |
| **Trajectory** | Funding/backing, roadmap ambition, adoption momentum |

### Step 5 — Deliver the assessment

Synthesize into a clear recommendation with the evidence that supports it.

---

## Output format

```
# Tech Radar: [Technology Name]

## Recommendation: [ADOPT / TRIAL / ASSESS / HOLD]

[3–4 sentence summary: what this technology is, the recommendation, and the
primary reason behind it]

## Maturity scorecard

| Dimension | Signal | Notes |
|-----------|--------|-------|
| Adoption | Strong/Moderate/Weak | [one-line evidence] |
| Ecosystem | Strong/Moderate/Weak | [one-line evidence] |
| Community | Strong/Moderate/Weak | [one-line evidence] |
| Stability | Strong/Moderate/Weak | [one-line evidence] |
| Documentation | Strong/Moderate/Weak | [one-line evidence] |
| Trajectory | Strong/Moderate/Weak | [one-line evidence] |

## Key evidence

### Who's using it in production
[Named companies/projects, what they use it for, at what scale]

### Strengths
- [Concrete strength with evidence]
- ...

### Risks & concerns
- [Concrete risk with evidence]
- ...

## Alternatives to consider
| Alternative | When to prefer it |
|-------------|-------------------|
| [Alt 1] | [one-line scenario] |
| [Alt 2] | [one-line scenario] |

## Sources
1. [Title](url) — [what this source contributed]
```

### Recommendation scale

- **ADOPT**: Proven in production at scale, strong ecosystem, stable APIs, low risk.
  Confident recommendation for most teams.
- **TRIAL**: Promising and functional, but evaluate in your specific context before
  committing. Good for new projects; risky for migrations.
- **ASSESS**: Interesting technology worth watching. Not ready for production bets yet —
  explore in side projects or spikes.
- **HOLD**: Significant risks, declining momentum, or better alternatives exist.
  Avoid new adoption; plan migration if already using.

Be calibrated. Most technologies are Trial or Assess — Adopt and Hold are strong claims
that need strong evidence. When in doubt, lean toward the more cautious rating and
explain what would move it up.
