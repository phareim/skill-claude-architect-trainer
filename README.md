# claude-quiz

An interactive Socratic quiz coach for the [**Claude Certified Architect — Foundations**](https://www.anthropic.com/learn) certification, packaged as a Claude Code skill.

Invoke `/claude-quiz` mid-task in any Claude Code session and you get one exam-style question grounded in whatever you're currently working on, coaching that walks through the reasoning (not just the answer), and a persistent SQLite log of every question you've seen so weak areas surface over time.

---

## What this is, and why it's different from flashcards

The official exam asks scenario questions where four plausible options each map to a real production tradeoff, and only one is defensible. Rote recall doesn't get you there — you have to build the *reasoning*. So this skill is built around a back-and-forth loop:

1. **Ask one question** keyed to a specific task statement from the official exam guide.
2. **Wait** for your answer (it won't auto-reveal).
3. **Judge** the answer — correct / partial / incorrect / skipped.
4. **Coach** by walking through the load-bearing principle, citing the relevant task statement, pointing to the right Anthropic course or docs section, and — when there's a relevant cue in your current conversation — tying the lesson back to what you're actively building.
5. **Log** the question, your answer, the judgment, and the coaching to a local SQLite DB.
6. Suggest the next move.

The "tie back to current work" step is the part flashcards can't do. If you're mid-edit of a `.mcp.json`, the skill will pick a Domain 2 question and frame it around the tool descriptions you just wrote. That grounding is the whole point.

---

## Installation

This skill is distributed as a single repo that you symlink into `~/.claude/skills/`. No package manager, no build step.

```bash
git clone git@github.com:phareim/skill-claude-architect-trainer.git ~/code/skill-claude-architect-trainer
ln -s ~/code/skill-claude-architect-trainer ~/.claude/skills/claude-quiz
```

That's it. Open any Claude Code session and `/claude-quiz` is now available.

Requirements: Python 3 (standard library only — uses the built-in `sqlite3` module).

---

## Initial setup

None required. On first invocation the skill auto-creates its database at `~/.claude/data/claude-quiz.db`. The schema is created lazily by every CLI command, so there's no `init` step to remember.

**Optional — change the DB location.** Useful if you want to sync progress across machines via Dropbox / iCloud / Syncthing / a private repo:

```bash
export CLAUDE_QUIZ_DB=~/Dropbox/claude-quiz.db
```

Set this in your shell rc so it persists. The script always reads `CLAUDE_QUIZ_DB` first and falls back to the default.

**Optional — fewer permission prompts.** Add the skill's bash patterns to your Claude Code allowlist so you aren't approving every DB call:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 /Users/<you>/.claude/skills/claude-quiz/scripts/quiz_db.py:*)"
    ]
  }
}
```

Goes in `~/.claude/settings.json`. Or run the `/fewer-permission-prompts` skill after a few sessions and it'll detect the pattern automatically.

---

## Using it for best effect

A few habits make this skill pay off:

- **Invoke it mid-task, not in a vacuum.** The context grounding is the value-add. If you just wrote an MCP server, type `/claude-quiz` right then — you'll get a Domain 2 question framed around the tools you just designed, and the coaching will reference your specific decisions. Far more sticky than answering an abstract question.
- **Don't ask for the answer.** When you're stuck, say "hint" or take a real guess. The skill will give you a narrower question or eliminate options instead of dumping the answer. Most of the learning happens in the moment of effort, not in reading the explanation.
- **Read your own coaching back.** Once a week or so, run `/claude-quiz summary --judgment incorrect` and `/claude-quiz summary --judgment partial`. Those rows are where you actually learn something; revisit them before they fade. Spaced repetition with the lessons *you* generated beats reviewing someone else's notes.
- **Chase coverage, then chase weakness.** Early on, use `/claude-quiz domains` and target whichever high-weight domain has the lowest Asked count — broad coverage first. Once every domain has a handful of answered questions, switch to `/claude-quiz weakest` to drill where you actually misjudge.
- **Mix difficulties.** `easy` builds recall, `medium` builds judgment, `hard` builds tradeoff reasoning, `exam-mode` rehearses the actual exam format. Spend most of your time in `medium`; warm up in `easy`; use `exam-mode` in the final week.
- **Many short sessions beat one long one.** Five questions a day across two weeks compounds way better than fifty questions in one evening, both for retention and for picking up cues from many different working contexts.

---

## Invocation cheatsheet

| Type | What happens |
|---|---|
| `/claude-quiz` | Scans your current conversation for a theme, picks a `medium` question, asks it. |
| `/claude-quiz domain 2` | Forces a Domain 2 (Tool Design & MCP) question. |
| `/claude-quiz mcp` (or `subagents`, `plan mode`, `batch`, `escalation`, `extraction`, …) | Topic word — picks the matching task statement. |
| `/claude-quiz easy` / `medium` / `hard` / `exam` | Adjusts difficulty. `exam-mode` is full A/B/C/D in official style. |
| `/claude-quiz scenario customer support` | Pulls from one of the 6 official exam scenarios. |
| `/claude-quiz weakest` | Picks a question in the domain with your worst pass rate. |
| `/claude-quiz domains` (or `table` / `dashboard`) | Prints the 5-domain × weight table with your live answer counts. |
| `/claude-quiz stats` | Numeric per-domain pass rates. |
| `/claude-quiz summary` | Reads back recent questions with your answers + coaching. Filter with `--domain N` or `--judgment incorrect`. |

Args combine: `/claude-quiz domain 4 hard`, `/claude-quiz mcp exam-mode`, etc.

---

## How the skill picks a question

When you invoke `/claude-quiz` without a topic, the skill walks recent conversation for cues — `.mcp.json`, `CLAUDE.md`, hooks, JSON schemas, escalation logic, scratchpads, etc. — and maps them to a specific task statement in the official exam guide. The mapping table is in [`SKILL.md`](./SKILL.md) and the full task-statement detail is in [`references/exam-domains.md`](./references/exam-domains.md).

If nothing in the conversation clearly maps, it falls back to a domain weighted by the official exam weighting (Domain 1: 27%, 2: 18%, 3: 20%, 4: 20%, 5: 15%), biased toward whichever domain currently has your lowest pass rate.

---

## Project layout

```
skill-claude-architect-trainer/
├── SKILL.md                              # the skill itself — read by Claude on invocation
├── references/
│   ├── exam-domains.md                   # full 5-domain × task-statement breakdown
│   ├── sample-questions.md               # the 12 official sample questions (templates for exam-mode)
│   └── anthropic-resources.md            # map from exam topic → Anthropic course / docs
├── scripts/
│   └── quiz_db.py                        # SQLite CLI: banner, domains, stats, summary, log, …
└── README.md                             # this file
```

The DB itself (`~/.claude/data/claude-quiz.db` by default) lives **outside** the repo, so your progress doesn't get committed.

---

## Sources

- Official exam guide: *Claude Certified Architect — Foundations Certification Exam Guide* (Anthropic, v0.1, Feb 2025). This is the primary source for every domain breakdown, task statement, sample question, and preparation exercise referenced by the skill.
- Anthropic Academy: <https://claude.com/resources/courses>
- Anthropic Learn: <https://www.anthropic.com/learn>
- Anthropic developer docs: <https://platform.claude.com/docs/en/home>

The skill's coaching cites only resources listed in [`references/anthropic-resources.md`](./references/anthropic-resources.md) — no invented deep URLs.

---

## Disclaimer

Built for personal exam preparation. Not affiliated with or endorsed by Anthropic. The exam guide referenced is Anthropic's official material; this skill organises it into a practice loop.
