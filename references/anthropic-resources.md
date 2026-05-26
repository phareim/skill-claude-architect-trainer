# Anthropic Learning Resources — Coaching Citation Map

When you coach an answer, point the user to a relevant Anthropic resource so they can study deeper. Cite only what's listed here — do not invent URLs.

## Top-level hubs (safe to cite always)
- **Anthropic Academy** — `https://claude.com/resources/courses` — all official courses, Skilljar platform, free, certificate on completion.
- **Anthropic Learn** — `https://www.anthropic.com/learn` — learning paths overview.
- **Anthropic docs** — `https://platform.claude.com/docs/en/home` — canonical reference for API, Claude Code, MCP, Agent SDK.

## Course → Domain map

| Course (on claude.com/resources/courses) | Most relevant exam content |
|---|---|
| **Claude 101** | Capabilities baseline, ambient knowledge for everything |
| **Claude Code 101** | Domain 3 (CLAUDE.md, slash commands, plan mode) |
| **Claude Code in Action** | Domain 3 hands-on; Domain 5 (codebase exploration, scratchpads, Explore subagent) |
| **Introduction to subagents** | Domain 1 (1.2 coordinator-subagent, 1.3 invocation, context passing) |
| **Introduction to agent skills** | Domain 3 (3.2 skills with `context: fork`, `allowed-tools`, `argument-hint`) |
| **Introduction to Claude Cowork** | Cowork-specific patterns (not directly tested but useful context) |
| **Building with the Claude API** | Domain 4 (4.3 `tool_use` + JSON schema, `tool_choice`); Domain 1 (1.1 `stop_reason` agentic loop); Domain 4.5 Message Batches |
| **Introduction to Model Context Protocol** | Domain 2 (2.1 tool design, 2.4 `.mcp.json` config, MCP resources) |
| **Model Context Protocol: Advanced Topics** | Domain 2 (2.2 structured errors with `isError`, `errorCategory`; resources for catalogs) |
| **AI Capabilities and Limitations** | Cross-cutting — lost-in-the-middle, hallucination, calibration intuitions (Domain 4.4, 4.6, 5.5) |
| **AI Fluency: Framework & Foundations** | Mental model for any AI collaboration question |
| **Claude with Amazon Bedrock** / **Vertex AI** | Out-of-scope per the exam guide — don't cite for exam prep |

## Docs section → Domain map

| Docs area (under platform.claude.com/docs) | Most relevant exam content |
|---|---|
| **Agent SDK** — agent definitions, hooks, the agentic loop | Domain 1.1, 1.3, 1.5 |
| **Tool use** — schemas, `tool_choice`, parallel tool use | Domain 2.1, 2.3, 4.3 |
| **MCP** — server config, tools, resources | Domain 2.4 |
| **Claude Code** — CLAUDE.md hierarchy, slash commands, skills, plan mode, `-p` flag | Domain 3 (entire) |
| **Prompt engineering** — XML structure, few-shot, chain of thought, prompt chaining | Domain 4.1, 4.2; Domain 1.6 |
| **Structured outputs / JSON mode** | Domain 4.3 |
| **Message Batches API** | Domain 4.5 |
| **Context window / context management** | Domain 5.1, 5.4 |
| **Extended thinking** | Aware of but de-emphasised in this exam (Domain 4.6 notes independent review beats extended thinking for self-review) |

## How to cite in coaching responses

Prefer concrete, falsifiable references:

> "This maps to **Task 2.1** in the exam guide — tool descriptions as the primary selection signal. The same idea is taught in the **Introduction to Model Context Protocol** course on Anthropic Academy, and detailed in the tool-use docs at platform.claude.com."

Avoid:
- Made-up deep URLs (anything beyond the three top-level hubs above unless you've verified it in this conversation).
- Vague "see the docs" without specifying which docs section.
- Citing courses that don't exist on the academy.

If unsure, default to "Anthropic Academy on claude.com/resources/courses — look for *<course name>*".

## Self-study sequence (suggest if user is far from ready)

Recommended order for the user who wants to build readiness from scratch:

1. **Claude Code in Action** — anchors Domain 3 hands-on.
2. **Introduction to Model Context Protocol** + **Advanced Topics** — anchors Domain 2.
3. **Introduction to subagents** — anchors Domain 1.
4. **Building with the Claude API** — anchors Domain 4 (tool_use, schemas, batches).
5. **AI Capabilities and Limitations** — intuition pump for Domain 5 reliability questions.
6. The four **Preparation Exercises** in the exam guide (build an agent with escalation logic, configure Claude Code for a team, build an extraction pipeline, design a multi-agent research pipeline).
7. The 12 sample questions in `references/sample-questions.md` — replay until correct + can explain why distractors fail.
