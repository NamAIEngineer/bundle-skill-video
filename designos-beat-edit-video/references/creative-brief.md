# Creative brief (the skill is NOT a fixed template)
Every video starts with `python engine/ideate.py plan --edits N --seed <new>`. It randomises concept, music style/bpm/key,
palette (dark or light), structure (cold open / title first / countdown), edit spacing and total length.
Then YOU (the agent) must:
1. Write the idea for THIS product in your own words: hook, one-line promise, outro/question. Never reuse an earlier video's concept or copy.
2. Pick the edits that show the product best (real, shipped features only), and a payoff that fits the concept.
3. Choose music: `--style house|lofi|trap|synthwave|cinematic|random`; try 2 seeds and keep the better one.
4. Record NEW footage for this video. Never reuse footage from an older video. Measure the raw times, write `times.json`, run `ideate.py build`.
5. Run `run.py validate`, then `all`. Check frames before delivering.
Concepts to draw from (invent more): on the beat, speedrun, before/after, one take, questions, count-in, typography.

## Marketing angle (required in every plan)
Before recording, write: (a) the ONE feature of design:os studio the video sells (only shipped ones, e.g. Claude Code builds a full screen in the canvas, edit text/layers live, Keep/Revert on agent changes), (b) the viewer and the pain (e.g. 'designers who wait on devs'), (c) the promise in one line, (d) the call to action (FREE, try it; 'source-available', never 'open-source'; no 'Figma killer'). The footage must prove (a) on screen.
