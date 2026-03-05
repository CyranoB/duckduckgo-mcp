---
name: tech-advisor
license: MIT
metadata:
  author: CyranoB
  version: "2.0.0"
description: >
  ALWAYS use this skill when a user needs help choosing between tech products or evaluating
  whether a technology is ready for adoption. This skill searches the web for current data
  and produces structured, evidence-based recommendations — something Claude cannot do well
  without it.

  Two modes: (1) Product comparison — "X vs Y", choosing between devices, editors, services,
  frameworks, headphones, laptops, keyboards, or any tech products. (2) Technology maturity
  assessment — "is X production ready", "should we adopt X", evaluating if a framework, tool,
  runtime, or library is stable enough for real use.

  Trigger on ANY of these patterns, even if the query seems simple enough to answer without
  a skill — the skill adds web research, structured comparison tables, and sourced evidence
  that raw Claude cannot provide:
  - Comparing two or more products: "MacBook vs ThinkPad", "Supabase vs Firebase",
    "RabbitMQ vs Kafka", "Sony WH-1000XM5 or Bose QC Ultra"
  - Evaluating readiness: "is Bun stable enough", "is htmx viable for production",
    "is Solid.js ready for a real app"
  - Asking what to choose: "help me pick a message broker", "which iPad for note-taking",
    "what code editor should I use"
  - Asking for a recommendation with context: "we're a 4-person startup evaluating X",
    "our CTO wants us to assess Y"

  Do NOT trigger for: general web research, news monitoring, fact-checking claims,
  competitive intelligence about companies, debugging code, or finding libraries.
---

# Tech Advisor

This skill helps users make technology decisions. It operates in two modes depending on
what the user needs:

- **Maturity assessment**: evaluate whether a technology (framework, language, tool) is
  ready for adoption. Produces an Adopt/Trial/Assess/Hold recommendation.
- **Product comparison**: compare specific tech products (devices, software, services) for
  a particular use case. Produces a side-by-side comparison with a recommendation.

Detect the mode from the user's query. If they mention a single technology and want to
know if it's ready/mature/worth adopting, use maturity assessment. If they mention two or
more products and want help choosing, or ask "what's the best X for Y", use product
comparison.

## Tools available

Use whatever search and fetch tools are available in your environment. In order of
preference:

1. **MCP tools** — if `mcp__duckduckgo__search` or `mcp__duckduckgo__jina_fetch` are
   available, use those.
2. **Built-in tools** — if your agent has a built-in web search tool (e.g., `WebSearch`,
   `web_search`, `search`) or a URL fetch tool (e.g., `WebFetch`, `fetch`), use those.
3. **Python ddgs library** — run a search via the `ddgs` package:
   ```python
   from ddgs import DDGS
   results = DDGS().text(query="your query", max_results=8)
   for r in results:
       print(r["title"], r["href"], r["body"])
   ```
   If `ddgs` isn't installed: `pip install ddgs`
4. **Jina Reader** — fetch any URL as clean markdown:
   ```bash
   curl -s "https://r.jina.ai/https://example.com"
   ```

The skill works with any combination of search + fetch. You need at least one way to
search the web and one way to read a URL's content.

**Freshness matters.** Tech products and technologies evolve fast — a 6-month-old review
can be outdated. Always include the current year in your search queries (e.g., "iPad Air
review 2026", "Deno production ready 2026"). When fetching sources, prefer articles
published within the last 6 months. If a source doesn't mention the latest version of a
product or technology, look for a more recent one.

---

## Mode 1: Maturity Assessment

Use this mode when the user wants to evaluate a single technology's readiness for adoption.

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

Pick 4-6 URLs across dimensions. Prioritize:
- Official project pages (for roadmap, stability claims)
- Case studies or blog posts from production users
- Community discussions (Reddit, HN) for unfiltered opinions
- Benchmark or comparison articles for performance claims

### Step 4 — Evaluate each dimension

| Dimension | What to look for |
|-----------|-----------------|
| **Adoption** | Named production users, company size, use case diversity |
| **Ecosystem** | Package count, key integrations, tooling quality |
| **Community** | Contributor count, issue response time, activity trends |
| **Stability** | Version history, breaking change frequency, LTS policy |
| **Documentation** | Official docs quality, tutorials, Stack Overflow coverage |
| **Trajectory** | Funding/backing, roadmap ambition, adoption momentum |

### Step 5 — Deliver the assessment

Use the **Maturity Assessment Output Format** below.

---

## Mode 2: Product Comparison

Use this mode when the user wants to choose between two or more specific products, or
asks "what's the best X for Y".

The key insight here: a good product comparison is opinionated and context-aware, not a
generic spec sheet. The user's specific needs, use case, and priorities should drive
which differences actually matter.

### Step 1 — Understand the user's needs

Before researching, make sure you know:
- **Products**: which specific products/models are being compared? If the user is vague
  ("an iPad"), help narrow it down to specific current models.
- **Use case**: what will they use it for? This is critical — it determines which specs
  and features actually matter.
- **Priorities**: what matters most? (price, performance, portability, durability, ecosystem...)
- **Context**: who is it for? (themselves, a gift, a team) Any constraints? (budget, existing ecosystem)

If the user already provided enough context (like "iPad vs iPad Air for my daughter's
note-taking at university"), don't over-interview — start researching.

### Step 2 — Targeted research

Search with the user's specific use case in mind. Generic "X vs Y" searches help, but
use-case-specific searches are more valuable:

**Head-to-head comparisons:**
- "[product A] vs [product B] [year]"
- "[product A] vs [product B] for [use case]"

**Use-case-specific reviews:**
- "best [product category] for [use case] [year]"
- "[product] review [use case]" (e.g., "iPad Air review note taking students")

**Real user experiences:**
- "[product] for [use case] reddit"
- "[product] student review" or "[product] long term review"

**Pricing & value:**
- "[product] price [region]" or "[product] deals [year]"
- "[product] accessories cost" (total cost of ownership matters)

### Step 3 — Fetch key sources

Pick 4-6 of the most relevant URLs. Prioritize:
- Detailed comparison articles from reputable tech reviewers
- Use-case-specific reviews (e.g., "best tablet for students")
- Reddit/forum threads with real user experience for this use case
- Official product pages for current specs and pricing

### Step 4 — Analyze through the user's lens

Don't just list specs — evaluate each difference through the lens of the user's stated
needs. A spec difference that's irrelevant to their use case shouldn't dominate the
comparison. Focus on:

- **What actually matters for their use case** — e.g., for note-taking: stylus support,
  screen quality, app ecosystem, weight, battery life
- **Real-world differences** — not just spec sheet numbers but how they translate to
  daily use
- **Total cost of ownership** — include essential accessories (stylus, keyboard, case)
- **Longevity** — how long will each option stay relevant for their needs?

### Step 5 — Deliver the comparison

Use the **Product Comparison Output Format** below.

---

## Maturity Assessment Output Format

```
# Tech Advisor: [Technology Name]

## Recommendation: [ADOPT / TRIAL / ASSESS / HOLD]

[3-4 sentence summary: what this technology is, the recommendation, and the
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

---

## Product Comparison Output Format

```
# Tech Advisor: [Product A] vs [Product B]

## Recommendation: [Product name]

[3-4 sentence summary: which product is recommended for this user's specific needs
and why. Be direct — "For note-taking at university, the iPad Air is the better
choice because..." not "it depends."]

## Quick comparison

| | [Product A] | [Product B] |
|---|---|---|
| Price (base) | | |
| [Key spec 1 for use case] | | |
| [Key spec 2 for use case] | | |
| [Key spec 3 for use case] | | |
| ... | | |

## What matters for [use case]

### [Most important factor]
[Which product wins on this factor and why, with evidence from reviews/user reports]

### [Second factor]
[Same structure]

### [Third factor]
[Same structure]

## Total cost of ownership
| Item | [Product A] | [Product B] |
|------|---|---|
| Device | $X | $Y |
| [Essential accessory 1] | $X | $Y |
| [Essential accessory 2] | $X | $Y |
| **Total** | **$X** | **$Y** |

## What you'd give up
[Brief, honest description of what the user loses by going with the recommended
option. Every choice has trade-offs — name them.]

## Sources
1. [Title](url) — [what this source contributed]
```

Adapt the comparison table columns and "what matters" sections to fit the specific
products and use case. The template above is a starting point — use your judgment about
which sections are relevant. A comparison of two laptops might need a battery life
section; a comparison of two APIs might not need total cost of ownership.

The goal is a recommendation the user can act on, backed by evidence they can verify.
Not a balanced-to-the-point-of-useless "both are good options" — take a position and
defend it, while being transparent about trade-offs.
