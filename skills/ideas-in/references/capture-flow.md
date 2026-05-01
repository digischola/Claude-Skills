# capture-flow

Detailed steps for `ideas-in capture`. Loaded only when the skill is in capture mode.

## Step 1: Classify the entry type

Choose the closest fit:

| Type | Signal |
|---|---|
| `client-win` | Quantified outcome from a specific client engagement. ("Thrive: +188% sales in 90 days.") |
| `insight` | Opinion / framework / mental model. ("Most LPs fail the 5-second test because they bury the offer.") |
| `experiment` | Something Mayank tried, with hypothesis + result. ("Tried moving phone above the fold. Bookings up 40% in 48h.") |
| `failure` | Something that didn't work + the lesson. ("Tested 3 hero variants. None beat the control. Why: the form was the bottleneck, not the headline.") |
| `build-log` | Status update on Mayank's own build / brand. ("Locked Path C. AI illustrations allowed for non-photographic on Digischola only.") |
| `client-comm` | A real exchange with a client that contains a quotable insight. ("Athil asked why the workshop page converts 3x the retreat page. Answer: workshop has one CTA, retreat has four.") |
| `observation` | Something noticed in the wild — not Mayank's experiment, not a client win. ("Justin Welsh dropped the threaded-CTA pattern this week.") |

If genuinely unclear, store as `observation` and tag for later reclassification.

## Step 2: Extract concrete entities

Pull these into structured fields (none required, all helpful for downstream drafting):

- **metrics** — numbers with units. (`{ "sales_lift": "+188%", "cpa_drop": "-37%" }`)
- **tools_named** — apps / services / models named. (`["Claude", "Perplexity", "Higgsfield"]`)
- **client_handle** — anonymized per `credentials.md`. Never use real client name unless the client has consented.
- **dates** — convert relative to absolute. ("yesterday" → ISO date.)

Apply accuracy-protocol: if a number is fuzzy, leave it BLANK with reason. Better blank than wrong.

## Step 3: Suggest pillar / channel / format

Use `channel-routing.md` to map type → likely pillar + likely channels + likely formats. These are SUGGESTIONS, not commitments. `draft-week` makes the final call.

Defaults:

| Type | Suggested channels | Format candidates |
|---|---|---|
| client-win | LinkedIn-text, X-thread, Instagram-carousel | LI-post, X-thread, IG-carousel |
| insight | LinkedIn-text, X-single | LI-post, X-tweet |
| experiment | LinkedIn-text, X-thread | LI-post, X-thread |
| failure | LinkedIn-text | LI-post (long-form vulnerability) |
| build-log | LinkedIn-text, X-thread, WhatsApp-status | LI-post, X-thread, WA-status |
| client-comm | LinkedIn-text | LI-post |
| observation | X-single, LinkedIn-text | X-tweet, LI-post |

## Step 4: Append via script

```bash
python3 /Users/digischola/Desktop/.claude/skills/ideas-in/scripts/capture.py \
  --brand-folder /Users/digischola/Desktop/Digischola \
  --type <type> \
  --raw-note "<exact note text>" \
  --suggested-pillar "<pillar>" \
  --channel-fit "linkedin,x" \
  --tags "tag1,tag2"
```

Script returns the new entry ID.

## Step 5: Echo back

Tell user: "Captured as `<id>` (type: `<type>`, pillar: `<pillar>`). Idea bank now has N raw entries."

Do not draft a post in this turn. Capture is its own atomic action.

## Anti-patterns

- Do NOT auto-draft after capture. Capture is read-only on draft state.
- Do NOT mix two ideas into one entry. If the note has two distinct ideas, capture twice.
- Do NOT invent metrics. Blank-when-uncertain wins.
