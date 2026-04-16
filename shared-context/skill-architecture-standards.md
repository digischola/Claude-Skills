# Skill Architecture Standards (7 Levels)

Every skill built, imported, or modified must follow these standards. Based on Anthropic's skill building guide and production-tested patterns across 20+ skills.

---

## Level 1: Core Structure

Every skill is a folder with this anatomy:

```
skill-name/
├── SKILL.md              (required — the brain)
├── references/            (optional — deep knowledge, loaded on demand)
├── scripts/               (optional — executable code for deterministic tasks)
├── assets/                (optional — templates, fonts, icons)
└── evals/                 (optional — test cases for measuring quality)
```

SKILL.md is the only required file. Everything else supports it.

---

## Level 2: Progressive Disclosure (The Golden Rule)

**SKILL.md must stay under 200 lines.** This is not arbitrary — it's how much context an LLM can efficiently scan to decide what to load next.

Three tiers of information loading:

| Tier | What | When Loaded | Size Limit |
|------|------|-------------|------------|
| 1 | YAML frontmatter (name + description) | Always in context | ~100 words |
| 2 | SKILL.md body (process steps) | When skill activates | Under 200 lines |
| 3 | References, scripts, assets | Only when a step needs them | Unlimited, but each file under 300 lines ideally |

Think of SKILL.md as a table of contents that tells Claude where to look. The actual detailed documentation goes into references/ and Claude only pulls it when needed, step by step.

If a reference file exceeds 300 lines, add a table of contents at the top.

---

## Level 3: YAML Frontmatter (Triggering)

The description field determines whether Claude activates the skill. Three components:

1. **What it does** — clear outcome description
2. **Trigger words** — specific phrases that should activate it (be "pushy" — undertriggering is the common failure mode)
3. **Anti-triggers** — what should NOT activate it (adjacent skills, similar keywords that mean something different)

Bad: `"Helps with marketing research"`
Good: `"Comprehensive pre-marketing business and market research for new client onboarding or new product launches. Use whenever user mentions: new client research, business analysis, market research, competitor analysis... Do NOT trigger for ad copy writing, campaign creation..."`

---

## Level 4: Business Personalization

A skill without business context produces generic output. Every skill must:

1. Read `shared-context/analyst-profile.md` at activation — this grounds the skill in Mayank's workflow, client types, quality standards, and formatting preferences
2. Reference any client-specific context if it exists (previous research, brand configs, positioning docs)
3. Produce outputs that match the analyst's voice and standards, not generic AI-report style

The shared context folder (`~/.claude/shared-context/` or `.claude/shared-context/`) is the single source of truth for business identity. Individual skills reference it — they don't duplicate it.

---

## Level 5: Evaluation & Benchmarking

Every skill should have test cases in `evals/evals.json`:

```json
{
  "skill_name": "skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user prompt",
      "expected_output": "What good looks like",
      "assertions": [
        {"name": "assertion_name", "description": "What to check"}
      ]
    }
  ]
}
```

Test cases should:
- Be realistic prompts a real user would type (not abstract descriptions)
- Cover different client types and edge cases
- Include 3-5 assertions per test (not too many — focused checks)
- Be runnable via the skill-creator's eval framework

Use evals to validate changes: run before/after when modifying a skill to confirm improvements.

---

## Level 6: Self-Improvement (Feedback Loop)

Every skill has a "Learnings & Rules" section at the bottom of SKILL.md:

```markdown
## Learnings & Rules
- [DATE] [CLIENT TYPE] Finding → Action
```

After every session using the skill:
1. Review output against the checklist
2. Capture what worked better/worse than expected
3. Add concise, actionable entries (not vague observations)
4. Keep under 30 lines — prune quarterly
5. Promote repeated patterns into reference files where they belong

The skill gets better with every use without manual eval runs.

---

## Level 7: Skill Coordination

Skills don't operate in isolation. They share context and feed each other:

### Shared Context (read by all skills)
- `shared-context/analyst-profile.md` — business identity, preferences, standards
- `shared-context/accuracy-protocol.md` — universal accuracy rules
- Client-specific brand configs and previous research

### Downstream Outputs
Every skill should produce outputs that other skills can consume:
- Structured JSON alongside human-readable reports
- Brand config files saved separately for reuse
- Clear section labeling so other skills can find specific data

### Cross-Skill Flagging
When a skill discovers something actionable by another skill, note it in the output:
- "This positioning gap is ready for meta-ad-copywriter skill"
- "This content gap could drive TOFU traffic — consider content calendar skill"

Don't do the other skill's job. Flag the connection and move on.

---

## Checklist for Every New Skill

Before considering a skill "done":

- [ ] SKILL.md under 200 lines
- [ ] YAML description includes triggers, anti-triggers, outcome
- [ ] Heavy detail lives in references/ (not crammed into SKILL.md)
- [ ] Reads shared-context/analyst-profile.md for personalization
- [ ] Follows accuracy-protocol.md for all data handling
- [ ] Has a Learnings & Rules section for feedback loop
- [ ] Outputs are structured for downstream skill consumption
- [ ] evals/evals.json has 2-3 realistic test cases
- [ ] Brand config saved as reusable JSON when applicable
