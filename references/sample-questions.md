# Official Sample Questions

Twelve questions from the official exam guide. These are the **canonical template** for exam-mode questions: realistic production context, four options, exactly one defensible answer, distractors that map to common misconceptions.

Use these to: (a) calibrate the style and depth of new questions, (b) replay verbatim if the user wants the official set, (c) point to the rationale when explaining why one option beats another.

---

## Scenario: Customer Support Resolution Agent

### Q1 — programmatic enforcement vs prompt instructions
> Production data shows that in 12% of cases, your agent skips `get_customer` entirely and calls `lookup_order` using only the customer's stated name, occasionally leading to misidentified accounts and incorrect refunds. What change would most effectively address this reliability issue?

- A) Add a programmatic prerequisite that blocks `lookup_order` and `process_refund` calls until `get_customer` has returned a verified customer ID.
- B) Enhance the system prompt to state that customer verification via `get_customer` is mandatory before any order operations.
- C) Add few-shot examples showing the agent always calling `get_customer` first, even when customers volunteer order details.
- D) Implement a routing classifier that analyses each request and enables only the subset of tools appropriate for that request type.

**Answer: A.** When a specific tool sequence is required for critical business logic, programmatic enforcement provides deterministic guarantees. B and C are probabilistic LLM compliance, insufficient when errors have financial consequences. D addresses tool availability, not ordering — wrong problem.

*Maps to:* Domain 1, Task 1.4 + 1.5 (programmatic enforcement over prompts when compliance is required).

---

### Q2 — tool descriptions as the primary selection signal
> Production logs show the agent frequently calls `get_customer` when users ask about orders (e.g., "check my order #12345"), instead of calling `lookup_order`. Both tools have minimal descriptions ("Retrieves customer information" / "Retrieves order details") and accept similar identifier formats. What's the most effective first step to improve tool selection reliability?

- A) Add few-shot examples to the system prompt with 5–8 examples showing order-related queries routing to `lookup_order`.
- B) Expand each tool's description to include input formats, example queries, edge cases, and boundaries explaining when to use it vs similar tools.
- C) Implement a routing layer that parses user input before each turn and pre-selects the appropriate tool based on detected keywords and identifier patterns.
- D) Consolidate both tools into a single `lookup_entity` tool that accepts any identifier and internally determines which backend to query.

**Answer: B.** Tool descriptions are the primary mechanism LLMs use for selection. B directly addresses the root cause with low-effort, high-leverage fix. A adds token overhead without fixing underlying issue. C is over-engineered, bypasses LLM language understanding. D is valid architecturally but more effort than a "first step".

*Maps to:* Domain 2, Task 2.1.

---

### Q3 — escalation calibration via explicit criteria
> Your agent achieves 55% first-contact resolution, well below the 80% target. Logs show it escalates straightforward cases (standard damage replacements with photo evidence) while attempting to autonomously handle complex situations requiring policy exceptions. What's the most effective way to improve escalation calibration?

- A) Add explicit escalation criteria to your system prompt with few-shot examples demonstrating when to escalate versus resolve autonomously.
- B) Have the agent self-report a confidence score (1–10) before each response and automatically route to humans when confidence falls below a threshold.
- C) Deploy a separate classifier model trained on historical tickets to predict which requests need escalation before the main agent begins processing.
- D) Implement sentiment analysis to detect customer frustration levels and automatically escalate when negative sentiment exceeds a threshold.

**Answer: A.** Explicit criteria + few-shot directly address the root cause (unclear decision boundaries) — proportionate first response. B fails: LLM self-confidence is poorly calibrated; agent is already incorrectly confident on hard cases. C over-engineered: needs labelled data + ML infra when prompt tuning untried. D wrong problem: sentiment ≠ case complexity.

*Maps to:* Domain 5, Task 5.2.

---

## Scenario: Code Generation with Claude Code

### Q4 — where project-scoped slash commands live
> You want to create a custom `/review` slash command that runs your team's standard code review checklist. This command should be available to every developer when they clone or pull the repository. Where should you create this command file?

- A) In the `.claude/commands/` directory in the project repository.
- B) In `~/.claude/commands/` in each developer's home directory.
- C) In the `CLAUDE.md` file at the project root.
- D) In a `.claude/config.json` file with a `commands` array.

**Answer: A.** Project-scoped custom slash commands live in `.claude/commands/`, version-controlled, automatically available to all developers. B is personal (not shared). C is for instructions, not command definitions. D describes a config mechanism that doesn't exist in Claude Code.

*Maps to:* Domain 3, Task 3.2.

---

### Q5 — when to use plan mode
> You've been assigned to restructure the team's monolithic application into microservices. This will involve changes across dozens of files and requires decisions about service boundaries and module dependencies. Which approach should you take?

- A) Enter plan mode to explore the codebase, understand dependencies, and design an implementation approach before making changes.
- B) Start with direct execution and make changes incrementally, letting the implementation reveal the natural service boundaries.
- C) Use direct execution with comprehensive upfront instructions detailing exactly how each service should be structured.
- D) Begin in direct execution mode and only switch to plan mode if you encounter unexpected complexity during implementation.

**Answer: A.** Plan mode is for complex tasks involving large-scale changes, multiple valid approaches, architectural decisions — exactly what monolith-to-microservices restructuring is. B risks costly rework when dependencies are discovered late. C assumes you already know the right structure. D ignores that complexity is already stated, not emergent.

*Maps to:* Domain 3, Task 3.4.

---

### Q6 — path-specific rules via `.claude/rules/`
> Your codebase has distinct areas with different coding conventions: React components use functional style with hooks, API handlers use async/await with specific error handling, and database models follow a repository pattern. Test files are spread throughout the codebase alongside the code they test (e.g., `Button.test.tsx` next to `Button.tsx`), and you want all tests to follow the same conventions regardless of location. What's the most maintainable way to ensure Claude automatically applies the correct conventions when generating code?

- A) Create rule files in `.claude/rules/` with YAML frontmatter specifying glob patterns to conditionally apply conventions based on file paths.
- B) Consolidate all conventions in the root `CLAUDE.md` file under headers for each area, relying on Claude to infer which section applies.
- C) Create skills in `.claude/skills/` for each code type that include the relevant conventions in their `SKILL.md` files.
- D) Place a separate `CLAUDE.md` file in each subdirectory containing that area's specific conventions.

**Answer: A.** `.claude/rules/` with glob patterns (`**/*.test.tsx`) allows conventions to apply automatically based on file paths regardless of directory — essential for test files spread throughout the codebase. B relies on inference (unreliable). C requires manual skill invocation. D can't easily handle files spread across many directories since CLAUDE.md is directory-bound.

*Maps to:* Domain 3, Task 3.3.

---

## Scenario: Multi-Agent Research System

### Q7 — narrow task decomposition is the root cause
> After running the system on the topic "impact of AI on creative industries," you observe that each subagent completes successfully: web search finds relevant articles, document analysis summarises papers correctly, synthesis produces coherent output. However, the final reports cover only visual arts, missing music, writing, and film production. The coordinator's logs show it decomposed the topic into three subtasks: "AI in digital art creation," "AI in graphic design," and "AI in photography." What is the most likely root cause?

- A) The synthesis agent lacks instructions for identifying coverage gaps in the findings it receives from other agents.
- B) The coordinator agent's task decomposition is too narrow, resulting in subagent assignments that don't cover all relevant domains of the topic.
- C) The web search agent's queries are not comprehensive enough and need to be expanded to cover more creative industry sectors.
- D) The document analysis agent is filtering out sources related to non-visual creative industries due to overly restrictive relevance criteria.

**Answer: B.** The coordinator's logs reveal the root cause: it decomposed "creative industries" into only visual arts subtasks, omitting music, writing, film. The subagents executed correctly within scope. A, C, D incorrectly blame downstream agents that are working within assignment.

*Maps to:* Domain 1, Task 1.2 (overly narrow decomposition risk).

---

### Q8 — structured error context for intelligent recovery
> The web search subagent times out while researching a complex topic. You need to design how this failure information flows back to the coordinator agent. Which error propagation approach best enables intelligent recovery?

- A) Return structured error context to the coordinator including the failure type, the attempted query, any partial results, and potential alternative approaches.
- B) Implement automatic retry logic with exponential backoff within the subagent, returning a generic "search unavailable" status only after all retries are exhausted.
- C) Catch the timeout within the subagent and return an empty result set marked as successful.
- D) Propagate the timeout exception directly to a top-level handler that terminates the entire research workflow.

**Answer: A.** Structured error context gives the coordinator the info it needs for intelligent recovery (retry modified query, alternative approach, proceed with partial results). B hides valuable context. C suppresses error by marking failure as success — prevents recovery. D terminates unnecessarily.

*Maps to:* Domain 5, Task 5.3.

---

### Q9 — scoped tool for high-frequency cross-role need
> During testing, you observe that the synthesis agent frequently needs to verify specific claims while combining findings. Currently, when verification is needed, the synthesis agent returns control to the coordinator, which invokes the web search agent, then re-invokes synthesis with results. This adds 2–3 round trips per task and increases latency by 40%. Your evaluation shows that 85% of these verifications are simple fact-checks (dates, names, statistics) while 15% require deeper investigation. What's the most effective approach to reduce overhead while maintaining system reliability?

- A) Give the synthesis agent a scoped `verify_fact` tool for simple lookups, while complex verifications continue delegating to the web search agent through the coordinator.
- B) Have the synthesis agent accumulate all verification needs and return them as a batch to the coordinator at the end of its pass, which then sends them all to the web search agent at once.
- C) Give the synthesis agent access to all web search tools so it can handle any verification need directly without round-trips through the coordinator.
- D) Have the web search agent proactively cache extra context around each source during initial research, anticipating what the synthesis agent might need to verify.

**Answer: A.** Applies principle of least privilege — gives the synthesis agent only what it needs for the 85% case while preserving existing coordination for complex cases. B creates blocking dependencies (synthesis steps may depend on earlier verified facts). C over-provisions, violates separation of concerns. D relies on speculative caching.

*Maps to:* Domain 2, Task 2.3 (scoped cross-role tools for high-frequency needs).

---

## Scenario: Claude Code for Continuous Integration

### Q10 — `-p` flag for non-interactive mode
> Your pipeline script runs `claude "Analyze this pull request for security issues"` but the job hangs indefinitely. Logs indicate Claude Code is waiting for interactive input. What's the correct approach to run Claude Code in an automated pipeline?

- A) Add the `-p` flag: `claude -p "Analyze this pull request for security issues"`.
- B) Set the environment variable `CLAUDE_HEADLESS=true` before running the command.
- C) Redirect stdin from `/dev/null`: `claude "Analyze this pull request for security issues" < /dev/null`.
- D) Add the `--batch` flag: `claude --batch "Analyze this pull request for security issues"`.

**Answer: A.** `-p` (`--print`) is the documented way to run Claude Code non-interactively. Outputs result to stdout and exits without waiting for input. The other options reference non-existent features (`CLAUDE_HEADLESS`, `--batch`) or Unix workarounds that don't address Claude Code's command syntax.

*Maps to:* Domain 3, Task 3.6.

---

### Q11 — Message Batches API: latency tolerance
> Your team wants to reduce API costs for automated analysis. Currently, real-time Claude calls power two workflows: (1) a blocking pre-merge check that must complete before developers can merge, and (2) a technical debt report generated overnight for review the next morning. Your manager proposes switching both to the Message Batches API for its 50% cost savings. How should you evaluate this proposal?

- A) Use batch processing for the technical debt reports only; keep real-time calls for pre-merge checks.
- B) Switch both workflows to batch processing with status polling to check for completion.
- C) Keep real-time calls for both workflows to avoid batch result ordering issues.
- D) Switch both to batch processing with a timeout fallback to real-time if batches take too long.

**Answer: A.** Message Batches API offers 50% cost savings but processing times up to 24 hours with no latency SLA — unsuitable for blocking pre-merge checks but ideal for overnight technical debt reports. B is wrong: "often faster" is unacceptable for blocking. C misconception: batch results can be correlated via `custom_id`. D adds unnecessary complexity.

*Maps to:* Domain 4, Task 4.5.

---

### Q12 — multi-pass review for attention dilution
> A pull request modifies 14 files across the stock tracking module. Your single-pass review analysing all files together produces inconsistent results: detailed feedback for some files but superficial comments for others, obvious bugs missed, and contradictory feedback — flagging a pattern as problematic in one file while approving identical code elsewhere in the same PR. How should you restructure the review?

- A) Split into focused passes: analyse each file individually for local issues, then run a separate integration-focused pass examining cross-file data flow.
- B) Require developers to split large PRs into smaller submissions of 3–4 files before the automated review runs.
- C) Switch to a higher-tier model with a larger context window to give all 14 files adequate attention in one pass.
- D) Run three independent review passes on the full PR and only flag issues that appear in at least two of the three runs.

**Answer: A.** Splitting reviews into focused passes addresses the root cause: attention dilution when processing many files at once. File-by-file ensures consistent depth; separate integration pass catches cross-file issues. B shifts burden to devs. C misunderstands — larger context windows don't solve attention quality. D would suppress detection of real bugs by requiring consensus on intermittently caught issues.

*Maps to:* Domain 4, Task 4.6 + Domain 1, Task 1.6.
