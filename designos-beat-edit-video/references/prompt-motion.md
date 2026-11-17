# Prompt Motion (motion ideas for every video)

Tools (MCP "Prompt Motion Bridge", available to Claude on Nam's Mac):
- `recommend_motion_references(brief, format="16:9"|"9:16", duration_seconds, style, limit<=5)` - ranks references for a brief (by titles/tags; it has not watched the videos).
- `search_motion_references(query, tags=[product-ui, phone, charts, diagrams, kinetic-type, shapes, particles, ...], limit<=8)` - search in Vietnamese or English.
- `get_motion_reference(slug)` - read the prompt, renderer/stack and links of one entry. Install commands in it are reference text only; never run them automatically.

Per video:
1. List the scenes that need motion: hook, transitions, chapter cards, callouts, captions, counters/stats, before/after, end card.
2. For each, search with NEW keywords and read the best 1-2 entries with get_motion_reference.
3. Choose >= 5 different references, rebuild the movement in our own code (PIL/numpy/ffmpeg, or Remotion if the reference is Remotion). Adapt to 16:9 or 9:16 and to the brand guardrails.
4. Write the slugs + what each one drove into the brief (`orca-briefs/<date>_<video>.md`). The next video must not reuse the same set.

Used so far (do not repeat as the main look):
- 2026-11-16 5-min tutorial: ryan-morr-ccc796, adamdesgns-478d6d, slvdev-64c45a, devius-maximus-beab45 (looked up by title only; the final look was bright cream + blobs, rise-in cards, bubble callouts, karaoke caption pill, wipe before/after).

Without the MCP (ChatGPT/ORCA/Codex): ask Claude or Nam for the reference list, or open prompt-motion.com yourself and write the chosen slugs in the brief. Do not claim a reference was used if it was not looked up.
