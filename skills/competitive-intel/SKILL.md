---
name: competitive-intel
license: MIT
metadata:
  author: CyranoB
  version: "2.0.0"
description: >
  ALWAYS use this skill when a user wants to understand a competitive landscape or
  position a product against competitors. Two modes: (1) Market landscape — user has a
  product idea or wants to map a market: "who are the competitors in X space", "I want
  to build a Y — what's out there", "market study for Z". (2) Competitive positioning —
  user has a product and wants strategic comparison: "how do we compare to competitors",
  "what are we missing vs the competition", "competitive analysis of our product".
  Trigger on: "competitive landscape", "market study", "who are the competitors",
  "competitive analysis", "I want to build X — what exists", "what are the alternatives
  to X", "how does X compare to the market", "gap analysis", "market map". Do NOT
  trigger for personal buying decisions (use tech-advisor), general web research,
  news monitoring, or fact-checking.
---

# Competitive Intel

This skill helps users understand competitive landscapes and position products
strategically. It's for people who are building or selling — not shopping.

There are two modes:

- **Market landscape**: the user has a product idea, is exploring a market, or wants
  to understand who the players are and where the opportunities lie.
- **Competitive positioning**: the user already has a product and wants to understand
  how it stacks up against specific competitors — what's missing, what's differentiated,
  where to invest next.

Detect the mode from the user's query. If they're asking "what's out there" or "who
are the competitors", it's landscape. If they're asking "how do we compare" or "what
are we missing vs X", it's positioning.

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

**Freshness matters.** Markets move fast — a year-old comparison can miss new entrants,
pricing changes, or pivots. Always include the current year in search queries. When
fetching sources, prefer articles published within the last 12 months.

---

## Mode 1: Market Landscape

Use this mode when the user wants to understand a market — either because they have a
product idea, are exploring an opportunity, or need to map the competitive terrain.

### Step 1 — Frame the market

Before searching, clarify:
- **Market definition**: what category or problem space? Be specific — "project management"
  is too broad; "project management for creative agencies" is useful.
- **User's angle**: are they exploring an idea, entering a market, or just trying to
  understand it? This shapes what matters most.
- **Scope**: B2B or B2C? What size companies? Geographic focus?

If the user gives enough context (like "I want to build a Notion competitor for
engineers"), don't over-interview — start researching.

### Step 2 — Multi-angle search

Search across these angles — each reveals a different layer of the market:

**Player discovery:**
- "[category] alternatives [year]"
- "[well-known player] competitors"
- "[category] market landscape [year]"
- "[category] comparison [year]"

**Market dynamics:**
- "[category] market size [year]"
- "[category] trends [year]"
- "[category] growth"

**Business models & pricing:**
- "[player A] pricing" / "[player B] pricing plans"
- "[category] pricing comparison"

**User sentiment & gaps:**
- "[well-known player] complaints reddit"
- "[well-known player] limitations"
- "[category] what's missing reddit"
- "switched from [player A] to [player B] why"

### Step 3 — Fetch key sources

Pick 5-8 URLs across angles. Prioritize:
- **Comparison/roundup articles** from reputable sources (G2, TechCrunch, industry blogs)
- **Official pricing pages** for top players (pricing is one of the most actionable data points)
- **Community discussions** (Reddit, HN, Indie Hackers) for unfiltered opinions and pain points
- **Market reports** or analyst coverage if available
- **Product Hunt or launch pages** for newer entrants

### Step 4 — Map the landscape

Organize your findings into a clear picture:

**Player categorization** — group competitors by tier or approach:
- Leaders (established, well-funded, large user base)
- Challengers (growing fast, differentiated approach)
- Niche players (serving specific segments well)
- Emerging (new entrants, early stage)

**Positioning analysis** — how does each player position themselves? What's their
primary value proposition? Who do they target? How do they price?

**Gap analysis** — based on user complaints, switching patterns, and underserved
segments, where are the opportunities? What problems aren't being solved well?

**Positioning map** — identify the two most important axes that differentiate players
in this market (e.g., general vs specialized, enterprise vs SMB, platform vs point
solution). Plot the players on a 2x2 text diagram. This makes the white space —
the underserved quadrant — immediately visible.

### Step 5 — Deliver the landscape report

Use the **Market Landscape Output Format** below.

---

## Mode 2: Competitive Positioning

Use this mode when the user has a product (or a specific product concept) and wants to
understand how it compares to named competitors.

### Step 1 — Understand the product and competitors

Before searching, clarify:
- **The user's product**: what does it do? Who's it for? What's the key differentiator?
- **Competitors to analyze**: which specific competitors? If the user hasn't named any,
  help identify the most relevant 3-5 based on a quick search.
- **What they want to learn**: feature gaps? Pricing positioning? Messaging differences?
  All of the above?

### Step 2 — Targeted research

Search with strategic intent — you're not just comparing specs, you're looking for
competitive advantage and blind spots:

**Head-to-head:**
- "[product] vs [competitor] [year]"
- "[product] alternative to [competitor]"

**Feature & capability gaps:**
- "[competitor] features list"
- "[competitor] changelog [year]" (what they've been shipping recently)
- "[competitor] roadmap" (where they're headed)

**Market perception:**
- "[competitor] review [year]"
- "[competitor] complaints" / "problems with [competitor]"
- "why I switched from [competitor] reddit"

**Pricing intelligence:**
- "[competitor] pricing [year]"
- "[competitor] enterprise pricing"

### Step 3 — Fetch key sources

Pick 4-6 URLs per competitor. Prioritize:
- **Official product/feature pages** for accurate capability data
- **Official pricing pages** for current pricing
- **Review sites** (G2, Capterra, TrustRadius) for structured pro/con data
- **Community threads** for real pain points and switching reasons
- **Competitor blog/changelog** for recent moves and direction

### Step 4 — Analyze strategically

Go beyond a feature checklist. For each competitor, assess:

- **Positioning overlap**: how much do they compete with you directly vs. serving
  a different segment?
- **Strengths to respect**: where are they genuinely better? Don't be dismissive —
  understanding competitor strengths helps you avoid their turf or invest to match.
- **Weaknesses to exploit**: where are their users frustrated? These are your
  opportunities.
- **Trajectory**: are they investing heavily in a direction that might collide with
  your roadmap? Or moving away?
- **Pricing position**: are they cheaper, more expensive, or similarly priced? What
  does their pricing model signal about their strategy?

### Step 5 — Deliver the positioning analysis

Use the **Competitive Positioning Output Format** below.

---

## Market Landscape Output Format

```
# Market Landscape: [Category/Market]

## Executive summary
[3-5 sentences: what this market looks like right now, how big it is (if data
available), key trends, and the most notable gap or opportunity]

## Market map

### Leaders
| Player | Positioning | Target audience | Pricing model | Est. scale |
|--------|-------------|-----------------|---------------|------------|
| [Name] | [one-line value prop] | [who they serve] | [free/freemium/$X/mo] | [users/revenue/funding if known] |

### Challengers
| Player | Positioning | Target audience | Pricing model | Est. scale |
|--------|-------------|-----------------|---------------|------------|

### Niche players
| Player | Positioning | Target audience | Pricing model | Est. scale |
|--------|-------------|-----------------|---------------|------------|

### Emerging
| Player | Positioning | Target audience | Pricing model | Est. scale |
|--------|-------------|-----------------|---------------|------------|

## Positioning map
[A text-based 2x2 matrix that plots players along the two axes most relevant to
this market. Choose axes that reveal where the white space is — e.g., "General
Purpose vs Specialized" and "Cloud-First vs Self-Hosted", or "Enterprise vs SMB"
and "Full Platform vs Point Solution". Place each player on the map and call out
where the gap is.]

## Pricing landscape
[Summary of how the market prices: what's the typical range? Free tier common?
Per-seat vs flat rate vs usage-based? Any pricing trends?]

## Gaps & opportunities
- [Underserved segment or unmet need, with evidence]
- [Common complaint about existing solutions]
- [Emerging trend that incumbents haven't addressed]
- ...

## Barriers to entry
- [What makes it hard to compete in this market — network effects, switching costs,
  data moats, regulatory, etc.]

## Key takeaways
[2-3 actionable insights for someone considering entering or investing in this market]

## Sources
1. [Title](url) — [what this source contributed]
```

---

## Competitive Positioning Output Format

```
# Competitive Analysis: [Your Product] vs the Market

## Executive summary
[3-5 sentences: where you stand, your strongest differentiators, and the most
important competitive gap to address]

## Competitive matrix

| Capability | [Your Product] | [Competitor A] | [Competitor B] | [Competitor C] |
|------------|---------------|----------------|----------------|----------------|
| [Key feature 1] | ... | ... | ... | ... |
| [Key feature 2] | ... | ... | ... | ... |
| Pricing (entry) | ... | ... | ... | ... |
| Pricing (pro/team) | ... | ... | ... | ... |
| Target audience | ... | ... | ... | ... |

## Per-competitor breakdown

### vs [Competitor A]
**Their positioning**: [how they describe themselves]
**Where they're stronger**: [honest assessment]
**Where you're stronger**: [with evidence]
**Their users complain about**: [real pain points from reviews/forums]
**Their recent moves**: [what they've shipped or announced recently]
**Threat level**: [High/Medium/Low — how much do they directly compete with you?]

### vs [Competitor B]
[Same structure]

## Pricing comparison
| Tier | [Your Product] | [Competitor A] | [Competitor B] | [Competitor C] |
|------|---------------|----------------|----------------|----------------|
| Free/Starter | ... | ... | ... | ... |
| Pro/Team | ... | ... | ... | ... |
| Enterprise | ... | ... | ... | ... |

[Commentary on pricing strategy: are you priced competitively? Is there a positioning
opportunity in pricing?]

## Your differentiators
[What genuinely sets you apart — not marketing claims, but real differences backed
by evidence from the research]

## Gaps to address
[Features or capabilities where competitors are ahead and users notice. Prioritized
by impact — what would move the needle most?]

## Strategic recommendations
1. [Actionable recommendation based on the analysis]
2. [Another recommendation]
3. [Another recommendation]

## Sources
1. [Title](url) — [what this source contributed]
```

Adapt both templates to fit the specific market and products being analyzed. The
templates are starting points — add or remove sections based on what's relevant. A
B2C consumer product comparison might not need "Enterprise pricing"; a developer tool
comparison might need a "Developer experience" section.

The goal is actionable strategic intelligence, not a generic report. Every section
should help the user make better decisions about where to invest, how to position,
and what to build next.
