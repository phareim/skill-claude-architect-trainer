# Claude Certified Architect — Foundations: Domain Reference

Source: official Anthropic exam guide (v0.1, Feb 2025). Pass score 720/1000. All questions multiple-choice. 6 scenarios exist; 4 are picked at random per exam sitting.

## Domain weightings

| # | Domain | Weight |
|---|---|---|
| 1 | Agentic Architecture & Orchestration | 27% |
| 2 | Tool Design & MCP Integration | 18% |
| 3 | Claude Code Configuration & Workflows | 20% |
| 4 | Prompt Engineering & Structured Output | 20% |
| 5 | Context Management & Reliability | 15% |

When picking questions and no other signal exists, weight by these percentages.

## The six exam scenarios

| # | Name | Primary domains |
|---|---|---|
| 1 | Customer Support Resolution Agent (Agent SDK + MCP, ≥80% first-contact, escalation) | 1, 2, 5 |
| 2 | Code Generation with Claude Code (slash cmds, CLAUDE.md, plan mode) | 3, 5 |
| 3 | Multi-Agent Research System (coordinator + search/analysis/synthesis/report subagents) | 1, 2, 5 |
| 4 | Developer Productivity (built-in tools + MCP) | 2, 3, 1 |
| 5 | Claude Code for CI/CD (`-p`, JSON output, PR review) | 3, 4 |
| 6 | Structured Data Extraction (JSON schemas, tool_use, validation) | 4, 5 |

## Domain 1 — Agentic Architecture & Orchestration (27%)

**1.1 Design and implement agentic loops for autonomous task execution**
- Loop lifecycle: send request → inspect `stop_reason` (`tool_use` vs `end_turn`) → execute tools → append results → next iteration.
- Tool results are appended to conversation history so the model can reason about the next action.
- Model-driven decisions (Claude picks next tool from context) vs pre-configured decision trees / fixed tool sequences.
- Anti-patterns: parsing natural-language signals to decide loop termination; arbitrary iteration caps as the *primary* stop mechanism; using assistant text content as a completion indicator.

**1.2 Orchestrate multi-agent systems with coordinator-subagent patterns**
- Hub-and-spoke: coordinator owns inter-subagent communication, error handling, and routing.
- Subagents have **isolated context** — they do not inherit the coordinator's conversation history automatically.
- Coordinator role: task decomposition, delegation, result aggregation, deciding which subagents to invoke for the query.
- Common failure: overly narrow task decomposition leading to incomplete coverage of broad topics.
- Partition scope across subagents (distinct subtopics or source types) to minimise duplication.
- Iterative refinement loops: coordinator evaluates synthesis for gaps and re-delegates with targeted queries.
- Route all subagent communication through the coordinator for observability and controlled flow.

**1.3 Configure subagent invocation, context passing, and spawning**
- `Task` tool is the spawning mechanism. `allowedTools` must include `"Task"` for a coordinator to invoke subagents.
- Subagent context must be **explicitly provided** in the prompt — no automatic inheritance.
- `AgentDefinition`: description, system prompt, tool restrictions per subagent type.
- `fork_session` for divergent exploration from a shared analysis baseline.
- Pass complete prior-agent findings in the next subagent's prompt (e.g., web results into synthesis).
- Use structured data formats to separate content from metadata (source URLs, doc names, page numbers) so attribution is preserved.
- Emit multiple `Task` calls in a single response to spawn parallel subagents; specify goals + quality criteria rather than step-by-step procedural instructions.

**1.4 Implement multi-step workflows with enforcement and handoff patterns**
- Programmatic enforcement (hooks, prerequisite gates) vs prompt-based guidance for ordering.
- Use deterministic enforcement when compliance is required (e.g., verify identity before financial ops). Prompt instructions alone have non-zero failure rate.
- Structured handoff protocols for mid-process escalation: customer details, root cause, recommended action.
- Decompose multi-concern requests into distinct items, investigate in parallel under shared context, synthesise unified resolution.

**1.5 Apply Agent SDK hooks for tool call interception and data normalisation**
- `PostToolUse` hook intercepts tool results before the model processes them.
- Pre-tool hooks intercept outgoing calls to enforce compliance (e.g., block refunds >$500, route to human escalation).
- Hooks = deterministic guarantees. Prompt instructions = probabilistic compliance.
- Use hooks to normalise heterogeneous formats (Unix timestamps, ISO 8601, numeric status codes) before the agent sees them.

**1.6 Design task decomposition strategies for complex workflows**
- Prompt chaining (fixed sequential pipeline) for predictable multi-aspect reviews (e.g., per-file analysis → cross-file integration pass).
- Dynamic adaptive decomposition for open-ended investigation (subtasks discovered as work progresses).
- Splitting code reviews into per-file local + separate cross-file integration avoids attention dilution.

**1.7 Manage session state, resumption, and forking**
- `--resume <session-name>` continues a specific prior conversation.
- `fork_session` creates independent branches from a shared baseline (e.g., compare two refactor approaches).
- When prior tool results are stale, starting fresh with an injected structured summary is more reliable than resuming.
- Inform the resumed session about specific file changes for targeted re-analysis.

## Domain 2 — Tool Design & MCP Integration (18%)

**2.1 Design effective tool interfaces with clear descriptions and boundaries**
- Tool descriptions are the **primary** signal the LLM uses for selection. Minimal descriptions → unreliable selection.
- Include input formats, example queries, edge cases, boundary explanations.
- Ambiguous/overlapping descriptions cause misrouting (e.g., `analyze_content` vs `analyze_document`).
- System prompt keywords can override well-written descriptions — review for unintended associations.
- Split generic tools into purpose-specific ones with defined I/O contracts (`extract_data_points`, `summarize_content`, `verify_claim_against_source`).
- Rename + redescribe to eliminate functional overlap (`analyze_content` → `extract_web_results`).

**2.2 Implement structured error responses for MCP tools**
- MCP `isError` flag is the primary failure signal.
- Distinguish: transient (timeouts, unavailable), validation (invalid input), business (policy violation), permission errors.
- Generic "Operation failed" prevents intelligent recovery decisions.
- Return structured metadata: `errorCategory`, `isRetryable`, human-readable description.
- `retriable: false` for business-rule violations + customer-friendly explanation.
- Local recovery in subagents for transient failures; propagate to coordinator only what cannot be locally resolved (with partial results + what was attempted).
- **Access failures ≠ valid empty results.** Don't conflate.

**2.3 Distribute tools appropriately across agents and configure tool choice**
- Too many tools (18 vs 4-5) degrades selection reliability by increasing decision complexity.
- Agents with off-specialisation tools tend to misuse them (e.g., synthesis agent attempting web search).
- Scope tools to role; provide limited cross-role tools for specific high-frequency needs.
- `tool_choice` options: `"auto"` (model may text instead), `"any"` (must call some tool), forced (`{"type":"tool","name":"..."}` — must call this specific one).
- Use forced selection to ensure a specific tool runs first (e.g., `extract_metadata` before enrichment).
- Replace generic tools (e.g., `fetch_url`) with constrained alternatives (e.g., `load_document` that validates URLs).

**2.4 Integrate MCP servers into Claude Code and agent workflows**
- Project-scope: `.mcp.json` (shared via VCS for team tooling).
- User-scope: `~/.claude.json` (personal/experimental).
- Env var expansion in `.mcp.json` (e.g., `${GITHUB_TOKEN}`) for credentials without committing secrets.
- All configured MCP server tools are discovered at connection time and simultaneously available.
- MCP **resources** expose content catalogs (issue summaries, doc hierarchies, DB schemas) to reduce exploratory tool calls.
- Prefer community MCP servers (e.g., Jira) over custom builds for standard integrations; reserve custom for team-specific workflows.
- Tool descriptions for MCP tools should be detailed enough that the agent doesn't prefer built-in tools like Grep over more capable MCP tools.

**2.5 Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively**
- Grep for **content** search (function names, error strings, imports).
- Glob for **path** patterns (`**/*.test.tsx`).
- Read/Write for full file ops; Edit for targeted modifications via unique anchor text.
- When Edit fails on non-unique matches, fall back to Read + Write.
- Build understanding incrementally: Grep entry points → Read to trace flows, rather than reading everything upfront.
- Trace function usage across wrapper modules: identify all exported names, then search each.

## Domain 3 — Claude Code Configuration & Workflows (20%)

**3.1 Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organisation**
- Hierarchy: user-level `~/.claude/CLAUDE.md` → project-level `.claude/CLAUDE.md` (or root `CLAUDE.md`) → directory-level subdirectory `CLAUDE.md` files.
- User-level applies only to that user — not shared via VCS.
- `@import` syntax references external files for modularity.
- `.claude/rules/` directory organises topic-specific rule files as an alternative to monolithic CLAUDE.md.
- `/memory` command verifies which memory files are loaded.
- Diagnose configuration issues: e.g., new teammate not receiving instructions because they're in user-level not project-level.

**3.2 Create and configure custom slash commands and skills**
- Project-scoped commands: `.claude/commands/` (shared via VCS).
- User-scoped commands: `~/.claude/commands/` (personal).
- Skills in `.claude/skills/` with `SKILL.md` and frontmatter: `context: fork`, `allowed-tools`, `argument-hint`.
- `context: fork` runs the skill in an isolated sub-agent context — prevents skill output from polluting main conversation.
- Personal skill customisation: create variants in `~/.claude/skills/` with different names so teammates aren't affected.
- `allowed-tools` restricts tool access during skill execution (e.g., limit to file writes to prevent destruction).
- `argument-hint` prompts for required parameters if invoked without args.
- Skills = on-demand task-specific workflows; CLAUDE.md = always-loaded universal standards.

**3.3 Apply path-specific rules for conditional convention loading**
- `.claude/rules/` files with YAML frontmatter `paths:` containing glob patterns activate conditionally.
- Path-scoped rules load only when editing matching files — reduces irrelevant context and token usage.
- Glob-pattern rules beat directory-level CLAUDE.md when conventions span multiple directories (e.g., `**/*.test.tsx` for tests regardless of folder).

**3.4 Determine when to use plan mode vs direct execution**
- Plan mode: complex tasks, multiple valid approaches, architectural decisions, multi-file modifications. Safe codebase exploration + design before committing.
- Direct execution: simple, well-scoped changes (single function fix, single-file validation tweak).
- Explore subagent isolates verbose discovery output and returns summaries.
- Common pattern: plan mode for investigation → direct execution for implementation.

**3.5 Apply iterative refinement techniques for progressive improvement**
- Concrete input/output examples > prose when descriptions are interpreted inconsistently.
- Test-driven iteration: write test suite, share failures to guide improvement.
- Interview pattern: have Claude ask clarifying questions to surface considerations before implementing.
- Interacting problems → single detailed message; independent problems → sequential.
- 2-3 examples to clarify transformation requirements.

**3.6 Integrate Claude Code into CI/CD pipelines**
- `-p` / `--print`: non-interactive mode (required for pipelines — without it the process hangs waiting for input).
- `--output-format json` + `--json-schema`: machine-parseable structured output.
- Include prior review findings in context when re-running after new commits — instruct to report only new/still-unaddressed issues.
- Provide existing test files in context so test generation avoids duplicates.
- Document testing standards, valuable criteria, available fixtures in CLAUDE.md.
- Session context isolation: the same session that generated code is less effective at reviewing it.

## Domain 4 — Prompt Engineering & Structured Output (20%)

**4.1 Design prompts with explicit criteria to improve precision and reduce false positives**
- Specific criteria > vague "be conservative" / "only report high-confidence".
- Define which issues to report (bugs, security) vs skip (minor style, local patterns).
- Concrete severity definitions with code examples per level.
- High false-positive rates undermine developer trust in accurate categories.
- Temporarily disable noisy categories while refining; re-enable once tuned.

**4.2 Apply few-shot prompting to improve consistency and quality**
- Most effective technique for consistently formatted, actionable output when instructions alone are inconsistent.
- 2-4 targeted examples for ambiguous scenarios — show reasoning for why one option was chosen over plausible alternatives.
- Demonstrate desired output format (location, issue, severity, suggested fix).
- Distinguish acceptable patterns from genuine issues to reduce false positives + enable generalisation.
- Enables generalisation to novel patterns beyond pre-specified cases.
- Reduces hallucination in extraction (informal measurements, varied document structures).

**4.3 Enforce structured output using tool use and JSON schemas**
- `tool_use` with JSON schema → most reliable approach for schema-compliant output. Eliminates syntax errors.
- `tool_choice`: `auto` (may return text), `any` (must call *a* tool), forced (`{"type":"tool","name":"..."}` — must call this one).
- Tool use eliminates **syntax** errors but not **semantic** ones (line items not summing, values in wrong fields).
- Schema design: required vs optional fields; enum + `"other"` + detail string for extensibility; nullable for fields that may genuinely be absent.
- Set `tool_choice: any` when multiple extraction schemas exist and document type is unknown.
- Force specific tool when ordering matters (`extract_metadata` before enrichment).
- Nullable fields prevent the model fabricating values to satisfy required fields.

**4.4 Implement validation, retry, and feedback loops for extraction quality**
- Retry-with-error-feedback: append specific validation errors to retry prompt.
- Retries are **ineffective when info is genuinely absent** (vs format/structural errors which they can fix).
- Track `detected_pattern` field in findings to enable analysis of dismissal patterns.
- Semantic errors (wrong fields, math mismatches) vs schema syntax errors (eliminated by tool use).
- Self-correction: extract `calculated_total` alongside `stated_total` to flag discrepancies; add `conflict_detected` booleans for inconsistent sources.

**4.5 Design efficient batch processing strategies**
- Message Batches API: 50% cost savings, up to 24-hour processing window, no latency SLA, **no multi-turn tool calling** in a single request.
- Appropriate for non-blocking latency-tolerant workloads (overnight reports, nightly test gen).
- **Inappropriate** for blocking workflows (pre-merge checks).
- `custom_id` correlates batch request/response pairs and identifies which to resubmit.
- Refine prompts on a sample before batch-processing large volumes — maximises first-pass success.
- Calculate batch frequency from SLA (e.g., 4-hour windows for 30-hour SLA with 24h batch processing).

**4.6 Design multi-instance and multi-pass review architectures**
- Self-review limited: model retains reasoning context from generation, less likely to question itself.
- Independent review instances (without generator context) catch subtle issues better than self-review or extended thinking.
- Multi-pass: per-file local + cross-file integration avoids attention dilution + contradictory findings.
- Verification passes: model self-reports confidence alongside each finding for calibrated routing.

## Domain 5 — Context Management & Reliability (15%)

**5.1 Manage conversation context to preserve critical information across long interactions**
- Progressive summarisation risks: condensing numerical values, percentages, dates, customer-stated expectations into vague summaries.
- "Lost in the middle": models reliably process beginning + end of long inputs, may omit middle findings.
- Tool results accumulate disproportionately (e.g., 40+ fields per order lookup, only 5 relevant).
- Pass complete conversation history in subsequent API requests for coherence.
- Extract transactional facts (amounts, dates, order IDs, statuses) into a persistent "case facts" block included in each prompt, outside summarised history.
- Trim verbose tool outputs to only relevant fields *before* accumulation.
- Place key findings summaries at the beginning + explicit section headers to mitigate position effects.

**5.2 Design effective escalation and ambiguity resolution patterns**
- Escalate on: explicit human request, policy gap/exception, inability to make meaningful progress.
- **Honor explicit human-agent requests immediately** without first attempting investigation.
- Sentiment-based escalation + self-reported confidence are unreliable proxies for case complexity.
- Multiple customer matches → ask for additional identifiers rather than heuristic selection.
- Few-shot examples in system prompt demonstrating when to escalate vs resolve.
- Acknowledge frustration while offering resolution when issue is within capability; escalate only if customer reiterates preference.

**5.3 Implement error propagation strategies across multi-agent systems**
- Structured error context (failure type, attempted query, partial results, alternative approaches) enables intelligent coordinator recovery.
- Distinguish access failures (timeouts → retry decisions) from valid empty results (successful queries with no matches).
- Generic statuses ("search unavailable") hide valuable context.
- Anti-patterns: silently suppressing errors (returning empty as success); terminating entire workflow on single failure.
- Local recovery in subagents for transient failures; propagate only errors that cannot be locally resolved + what was attempted.
- Structure synthesis output with coverage annotations (which findings well-supported vs which topics have gaps).

**5.4 Manage context effectively in large codebase exploration**
- Context degradation in extended sessions: inconsistent answers, references to "typical patterns" rather than discovered specifics.
- Scratchpad files persist key findings across context boundaries.
- Subagent delegation isolates verbose exploration; main agent coordinates high-level understanding.
- Structured state for crash recovery: each agent exports state to a known location; coordinator loads manifest on resume.
- Summarise key findings before spawning next-phase sub-agents, inject summary into their initial context.
- `/compact` reduces context usage during long sessions.

**5.5 Design human review workflows and confidence calibration**
- Aggregate accuracy (97% overall) may mask poor performance on specific document types or fields.
- Stratified random sampling for measuring error rates in high-confidence extractions; detects novel error patterns.
- Field-level confidence calibrated using labelled validation sets to route review attention.
- Validate accuracy by document type + field segment before automating high-confidence extractions.
- Route low-confidence / ambiguous extractions to human review to prioritise limited capacity.

**5.6 Preserve information provenance and handle uncertainty in multi-source synthesis**
- Source attribution lost during summarisation when claim-source mappings aren't preserved.
- Synthesis agent must preserve + merge structured claim-source mappings.
- Conflicting statistics from credible sources: annotate conflicts with source attribution; don't arbitrarily pick one.
- Require publication/collection dates in structured outputs to prevent temporal differences appearing as contradictions.
- Distinguish well-established findings from contested ones in synthesis reports.
- Pass conflicting values + annotations to coordinator; let it decide how to reconcile before synthesis.
- Render content types appropriately (financial data → tables, news → prose, technical → structured lists) rather than uniform format.

## In-scope concepts (appendix)

Agent SDK • MCP • Claude Code • Claude Code CLI (`-p`, `--output-format json`, `--json-schema`) • Claude API (`tool_use`, `tool_choice`, `stop_reason`, `max_tokens`, system prompts) • Message Batches API • JSON Schema • Pydantic • Built-in tools • Few-shot • Prompt chaining • Context window management • Session management (`--resume`, `fork_session`) • Confidence scoring

## Out-of-scope (won't appear on the exam)

Fine-tuning • Auth/billing/account mgmt • Language-specific impl details • Hosting MCP servers • Claude internals/training • Constitutional AI/RLHF • Embeddings/vector DBs • Computer use • Vision • Streaming/SSE • Rate limits & pricing • OAuth/key rotation • Specific cloud provider configs • Benchmarking • Prompt caching internals • Tokenisation specifics
