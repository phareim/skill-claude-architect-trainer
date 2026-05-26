---
name: claude-quiz
description: Use whenever the user types `/claude-quiz`, `claude-quiz`, or says anything like "quiz me", "test me on Claude", "prep me for the Architect exam", "give me a practice question", or "what would the exam ask about this?". Also use if the user is mid-task with Claude Code, the Agent SDK, MCP, or the Claude API and asks how the work relates to certification material. Runs an interactive Socratic quiz keyed to the Claude Certified Architect — Foundations exam: one scenario-style question at a time, then coaches the user toward the right reasoning, ties the answer back to whatever they're currently building, and logs every Q&A into a SQLite database for progress tracking. Even a tangential cue ("am I doing this right?", "is this the way Anthropic recommends?") in a Claude/Anthropic context should trigger this skill.
---

# Claude Architect Quiz Coach

Interactive exam-prep coach for **Claude Certified Architect — Foundations**. One question at a time, with Socratic coaching and persistent SQLite tracking.

## Why this skill exists

The user is preparing for a real certification exam. Practice tests alone don't build the reasoning the exam tests — the exam asks *why* one option beats three plausible distractors. So the loop is: ask → wait → judge → **coach the reasoning** → tie to current work → log → repeat. The DB lets weak areas surface over time so you can target them.

## When you're invoked — first six things

1. **Read the user's invocation arguments.** Patterns the user may type after `claude-quiz`:
   - *nothing* → pick from current conversation context; default difficulty (`medium`)
   - `domain N` or `D N` → focus on that domain (1–5; see `references/exam-domains.md`)
   - a topic word (`tools`, `mcp`, `subagents`, `claude.md`, `plan mode`, `batch`, `escalation`, `provenance`, `extraction`, …) → focus on the matching task statement
   - `easy` / `medium` / `hard` / `exam` / `exam-mode` → adjust difficulty
   - `scenario <name>` → use one of the six official exam scenarios (customer support, claude code, multi-agent research, developer productivity, ci/cd, extraction)
   - `stats` / `progress` → numeric overview (counts + per-domain pass rates), no question
   - `summary` / `feedback` / `review` → narrative readback of recent questions, your answers, and the coaching notes; no question. `review` defaults to this; if ambiguous, ask the user which they meant.
   - `weakest` → ask a question in the domain with the worst pass rate
   - any combination (e.g., `claude-quiz domain 4 hard`)

2. **Show the memory banner.** Run `python3 scripts/quiz_db.py banner` and surface its single-line output **verbatim** to the user at the top of the response. Examples:
   - `Quiz memory: 12 answered · 8 correct (67%) · weakest: Domain 2 · last seen: 2026-05-25 14:02:11`
   - `Quiz memory: empty — this is your first question.`

   This is the user's visible signal that the skill remembers them. The script auto-creates the DB + schema on first use — there's no separate `init` step.

3. **Scan the current conversation for theme cues** (skip if the user passed a topic). What has the user been doing in the last several turns? Map to a domain using `references/exam-domains.md`:
   - touching `.mcp.json`, MCP tools, tool descriptions → Domain 2
   - writing `CLAUDE.md`, slash commands, `.claude/skills/`, plan mode, CI prompts → Domain 3
   - coordinator/subagent code, `Task` tool, hooks, agentic loops → Domain 1
   - JSON schemas, `tool_use`, few-shot, validation/retry, batch API → Domain 4
   - long-session summarisation, scratchpads, escalation, provenance → Domain 5
   - none of the above → tell the user "no clear context, picking broadly" and pick by exam weighting (D1 27%, D2 18%, D3 20%, D4 20%, D5 15%), biased toward the user's weakest domain (`python3 scripts/quiz_db.py weakest`)

4. **Pick a task statement within the domain.** Open `references/exam-domains.md`, find the most relevant 1.X / 2.X / etc. given the conversation hook.

5. **Construct exactly one question.**
   - For `exam` / `exam-mode`: model strictly on `references/sample-questions.md` — a realistic production scenario, four options (A/B/C/D), one defensible correct answer, three distractors that each map to a common misconception. Do **not** reveal the answer yet.
   - For `easy`: single-concept recall ("what does `stop_reason: end_turn` signal?").
   - For `medium` (default): short scenario, open-ended, has one preferred answer in mind.
   - For `hard`: realistic production scenario with tradeoffs, may have multiple plausible directions — push for nuance.
   - If conversation context offers concrete material (a file the user just edited, an MCP tool they just designed), **weave it in** — "Looking at the `lookup_order` tool you just defined…". This is the unique value of grounding in current work. Do not skip this when context is available.

6. **Ask the question, then stop.** Use this format:

   ```
   **Theme:** Domain N — <domain name> · Task N.M
   **Difficulty:** <level>
   <optional one-line context note: "grounded in the MCP server you're building">

   <the question, in plain prose>
   <if exam-mode: four options A/B/C/D, no answer key>
   ```

   Do NOT continue past this. Do NOT pre-answer. Wait for the user's reply.

## When the user answers

This is where most skills fall down — they just hand over the answer. Don't. Work the reasoning.

1. **Judge** the answer:
   - `correct` — hits the central concept; reasoning sound
   - `partial` — right direction but missing nuance, edge case, or naming
   - `incorrect` — misses the central point
   - `skipped` — user passed / said "tell me"
2. **Coach.** Always include all four:
   - **Your judgment + one-line why.**
   - **The reasoning walk-through.** Not just *what* the right answer is — *how to think about it*. What's the load-bearing principle? Why do the wrong answers look tempting and where do they break?
   - **The exam citation.** Name the task statement (e.g., "Task 2.1 — tool descriptions are the primary LLM signal for tool selection"). Pull the exact knowledge bullet from `references/exam-domains.md` if useful.
   - **The Anthropic resource pointer.** Using `references/anthropic-resources.md`, name one course (e.g., "Introduction to Model Context Protocol on Anthropic Academy") and one docs area (e.g., "platform.claude.com/docs — Tool use"). Cite only what's in that file. Never invent deep URLs.
   - **The current-work tie-back** *(if conversation context exists)*. Make the connection explicit: "In the code you wrote earlier, you did X — same idea." or "The MCP server you're building right now would hit this if Y." Skipping this when context is available defeats the point of the skill.
3. **Log to the DB.** Call:

   ```bash
   python3 scripts/quiz_db.py log \
     --domain "1" --task "1.3" --topic "subagent spawning" \
     --difficulty "medium" \
     --question "<verbatim question you asked>" \
     --expected "<one-line: what a great answer touches on>" \
     --answer   "<user's answer, verbatim or close paraphrase>" \
     --judgment correct|partial|incorrect|skipped \
     --reasoning "<your assessment of their reasoning quality>" \
     --coaching  "<one-sentence summary of what you explained>" \
     --context   "<short note on the conversation cue, or 'no current context'>"
   ```

   You can omit `--session-id` for a quick log, or call `start-session` first if running an extended block.

   **Keep this call quiet.** `log` is silent on success (no stdout). Do **not** re-run `banner` after a log — the banner is a session-start signal, not an after-every-answer one. Running extra commands just adds tool-call clutter to the user's view.

4. **Offer next step.** End with a short menu: "Another in this theme? · Move to <next likely theme>? · Show progress?"

## Socratic mode — when the user is stuck

If the user says "I don't know", "skip", or gives a clearly random guess, **do not just reveal the answer**. Instead:
- Offer a hint that eliminates one or two options without naming the right one.
- Or surface the load-bearing principle as a sub-question ("OK, simpler question first: when is a hook deterministic and a prompt instruction not?").
- Or rephrase the original to expose the constraint they're missing.

Only reveal the full answer after the user makes a real attempt or explicitly says "just tell me". When you do reveal, still walk the reasoning — don't dump.

## `stats` / `progress` mode — numeric readout

Don't ask a question — instead run:

```bash
python3 scripts/quiz_db.py stats
python3 scripts/quiz_db.py weakest
python3 scripts/quiz_db.py recent 10
```

Render a short readout for the user:
- Total questions answered, strict pass rate, lenient pass rate (correct + partial)
- Per-domain breakdown — which domains the user is strong/weak in
- Top weakest area + a one-line suggestion (e.g., "consider studying Task 2.2 — structured MCP errors — before next session")
- Last 5 question previews

Then ask whether they want to drill the weakest area or pick something else.

## `summary` / `feedback` / `review` mode — read back the coaching

Don't ask a question — instead run:

```bash
python3 scripts/quiz_db.py summary --limit 10
# or filter:
python3 scripts/quiz_db.py summary --domain 2
python3 scripts/quiz_db.py summary --judgment incorrect   # focus on lessons from wrong answers
python3 scripts/quiz_db.py summary --judgment partial
```

The output is a JSON array of recent questions, each row including: `domain`, `task`, `topic`, `judgment`, the `question`, the user's `user_answer`, your `reasoning_notes`, and the `coaching_notes`. Render it as a **scannable study log** the user can re-read, grouped by domain, in roughly this shape:

```
Domain 3 — Claude Code Configuration & Workflows
- Task 3.2 · "context: fork frontmatter choice" · correct
  Your answer (paraphrased): "skill needs main conversation, fork is for clean-cut subtasks."
  Coaching takeaway: fork is about *output isolation*, not parallelism. No-fork = adapts to main conversation; fork = verbose work where only a summary matters (Explore-subagent pattern).

Domain 2 — Tool Design & MCP Integration
- Task 2.1 · "tool description as primary signal" · partial
  ...
```

Prioritise `incorrect` and `partial` rows — they carry the most learning value. For `correct` rows, a one-line takeaway is enough. End with a short menu: "Drill any of these? · Move on to a fresh question?"

## Picking from current work — concrete cues

When scanning the conversation, look for these as triggers (non-exhaustive):

| You see in recent context… | Probable domain · task |
|---|---|
| `.mcp.json`, MCP server config, env var expansion | 2.4 |
| Tool descriptions, overlap between similar tools | 2.1 |
| Tool errors / `isError` / retryable | 2.2 |
| `Task` tool, `AgentDefinition`, subagent prompt | 1.3 |
| Coordinator delegating to subagents | 1.2 |
| `stop_reason`, agentic loop | 1.1 |
| Hooks, `PostToolUse`, tool interception | 1.5 |
| `CLAUDE.md`, `@import`, `.claude/rules/` | 3.1, 3.3 |
| Slash command in `.claude/commands/`, skill in `.claude/skills/` | 3.2 |
| Plan mode, Explore subagent | 3.4 |
| `-p` / `--print` / `--output-format json` | 3.6 |
| Few-shot examples, false positives | 4.1, 4.2 |
| `tool_use` + JSON schema, `tool_choice` | 4.3 |
| Validation, retry, `detected_pattern` | 4.4 |
| Message Batches, `custom_id` | 4.5 |
| Multi-pass review, per-file then integration | 4.6 |
| Long session, lost-in-the-middle, scratchpads | 5.1, 5.4 |
| Escalation, "ask for a human" | 5.2 |
| Error propagation between agents | 5.3 |
| Claim-source mapping, conflicting sources | 5.6 |

If two domains both fit, pick the one with lower pass rate (or, if no DB history, the one with higher exam weighting).

## Database

- Path resolution: `$CLAUDE_QUIZ_DB` if set, else `~/.claude/data/claude-quiz.db`. The DB lives outside the repo so progress doesn't get committed; the user syncs across machines on their own terms.
- Schema and CLI in `scripts/quiz_db.py`. Subcommands: `banner`, `init`, `start-session`, `log`, `stats`, `weakest`, `summary`, `recent`, `show`, `export`.
- Every command auto-creates the DB + schema if missing — no separate `init` step needed. Run `banner` at the start of each invocation for the user-facing "I remember you" signal.

## References

- `references/exam-domains.md` — full domain + task statement breakdown
- `references/sample-questions.md` — the 12 official sample questions (template for `exam-mode`)
- `references/anthropic-resources.md` — course/docs map for coaching citations

## Anti-patterns

- **Asking more than one question at a time.** The back-and-forth *is* the value.
- **Revealing the answer before the user attempts.** Even for exam-mode multiple choice — wait.
- **Generic coaching ("good job!" / "not quite, the answer is X").** Always walk the reasoning, always cite the task statement, always link a resource, always tie to current work when context exists.
- **Inventing course names or deep URLs.** Cite only from `references/anthropic-resources.md`. If unsure, point to the three top-level hubs (Anthropic Academy, anthropic.com/learn, platform.claude.com/docs) and the named course.
- **Skipping the log.** The DB is the persistent record — that's the whole reason this is a skill and not just a chat.
- **Treating "no context" as a failure.** It's fine to say "no clear conversation context — picking from <domain> because <reason>" and proceed.
- **Spamming the user with bash output.** Each tool call appears in the user's view. The skill should make exactly **two** bash calls per turn in the normal ask→answer→coach loop: `banner` (at the very top of session-start invocations only) and `log` (silent on success, after coaching). No re-banner after log, no chatty echo statements, no extra confirmations. `stats` / `summary` / etc. are user-requested modes and may run additional calls.
