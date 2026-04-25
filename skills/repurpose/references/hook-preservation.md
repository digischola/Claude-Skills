# Hook Preservation Rules

Core principle: the source hook is the reason the post worked (or is expected to work). Repurpose preserves it across channels, adapting only the wrapper.

## Default: PRESERVE

The source hook's **core claim**, **specific numbers**, and **concrete nouns** carry over verbatim to every variant.

Example source hook (LinkedIn):
> "188% more Meta sales. 37% lower cost per sale. 90 days, same client."

Preserved across:
- **X thread tweet 1:** "188% more Meta sales. 37% lower cost per sale. Same audience. Same ad budget. 90 days. One landing page rebuild. Here is what we changed."
- **IG carousel slide 1:** "188% more Meta sales. 37% lower CPS." (as title), full hook in caption
- **IG Reel voiceover:** "188% more sales. 37% lower cost per sale. Same budget. Here is what we changed." (spoken + on-screen text)
- **WhatsApp Status:** "Today's drop: a wellness client's LP went from 1.2% to 2.4% conversion in 48 hours."

The wrapper changes. The substance (188%, 37%, 90 days, landing page) survives.

## When to adapt the hook

Only adapt when one of these conditions fires:

### 1. Length overflow
Source hook is 150 chars. Target is X single tweet where the hook must be ≤240 chars including padding. Adapt: compress, never drop specifics.

### 2. Channel-native opener requirement
Instagram Reels demand a hook in the first 1.5 seconds (spoken, not read). A 20-word LinkedIn hook becomes a 5-word spoken opener + 15-word on-screen reinforcement.

### 3. Conservative attribution rewrite
If the source LI post named "Thrive Retreats" as a site-repost and the target channel (X) will reach a broader audience where the Conservative client-naming policy kicks in, rewrite "Thrive Retreats" to "a wellness retreat client in NSW Australia" in the variant.

### 4. Format demands (carousel titles)
IG carousel slide 1 uses large display-style text. A full sentence hook compresses to 4-8 words. Example:
- LI: "188% more Meta sales. 37% lower cost per sale."
- Carousel slide 1: "188% MORE SALES" (large text). Rest of hook in caption.

## When NOT to adapt

- Do not generate a new hook. That is post-writer's job.
- Do not rewrite the hook "because the user might prefer a different angle on X." If they want a different angle, they run post-writer fresh.
- Do not swap specific numbers for ranges or "significant lift" generic phrasing. The specifics are the hook.

## Hook adaptation reports

In each variant's frontmatter, log whether the hook was preserved or adapted:

```yaml
hook_preservation: preserved
# OR
hook_preservation: adapted (reason: char overflow; compressed from 175 to 240 chars for X-single)
```

This lets the user see at a glance which variants drifted from the source hook and why.

## Multi-variant test exception

If the user explicitly passes `--hook-mode new` for a specific target, the skill generates 3 fresh hook candidates for that variant (post-writer behavior) instead of preserving. Default is `--hook-mode preserve`. Document the override in frontmatter.

## Specifics that MUST survive every transformation

1. **Numerical claims:** 188%, 37%, 90 days, 1.2%, $1B, etc.
2. **Verbatim client-adjacent phrases that carry the narrative:** "landing page was the choke point", "a good ad funneling real buyers into a bad door"
3. **Tool names:** Claude, Perplexity, Lovable, Remotion
4. **Credential anchors if present in source:** Ex-Google, $1B+ managed (only if source anchored them)
5. **The closing question or observation** (channel-adapted only for word count, not substance)

Lose any of these and the variant is not a repurpose. It is a rewrite.
