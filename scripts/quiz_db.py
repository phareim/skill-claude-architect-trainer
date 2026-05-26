#!/usr/bin/env python3
"""SQLite store for the claude-quiz skill.

Subcommands:
  banner                        one-line memory signal (plain text, used at session start)
  domains                       5-domain markdown table with per-domain answer counts (plain text)
  init                          create DB + schema (also auto-runs on every other command)
  start-session                 record a new quiz session
  log                           log one question + judgment
  stats                         aggregate counts + per-domain pass rate
  weakest                       3 weakest domains by pass rate (for theme picking)
  summary [--limit N]           recent questions with answer + coaching readback
  recent [N]                    last N question previews
  show <id>                     full detail of one question
  export <path>                 dump all questions as JSON

DB path resolution order:
  1. $CLAUDE_QUIZ_DB if set
  2. ~/.claude/data/claude-quiz.db  (default — outside the repo so progress
     isn't committed; user syncs across machines on their own terms)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


def resolve_db_path() -> Path:
    if env := os.environ.get("CLAUDE_QUIZ_DB"):
        return Path(env).expanduser()
    return Path("~/.claude/data/claude-quiz.db").expanduser()


DB_PATH = resolve_db_path()

# Canonical exam domains (number, name, weight%). Single source of truth used
# by the `domains` subcommand so the SKILL.md / model never has to invent names.
DOMAINS = [
    ("1", "Agentic Architecture & Orchestration",   27),
    ("2", "Tool Design & MCP Integration",          18),
    ("3", "Claude Code Configuration & Workflows",  20),
    ("4", "Prompt Engineering & Structured Output", 20),
    ("5", "Context Management & Reliability",       15),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT,
    context_summary TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    asked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    domain TEXT NOT NULL,
    task TEXT,
    topic TEXT,
    difficulty TEXT,
    question TEXT NOT NULL,
    expected_answer TEXT,
    user_answer TEXT,
    judgment TEXT,
    reasoning_notes TEXT,
    coaching_notes TEXT,
    related_context TEXT
);

CREATE INDEX IF NOT EXISTS idx_questions_domain ON questions(domain);
CREATE INDEX IF NOT EXISTS idx_questions_judgment ON questions(judgment);
CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def emit(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


# ---------- commands ----------

def cmd_init(_):
    connect().close()
    emit({"ok": True, "db": str(DB_PATH)})


def cmd_banner(_):
    """One-line plain-text memory signal — printed verbatim by SKILL.md.

    Plain text (not JSON) so it can be surfaced to the user as-is.
    """
    con = connect()
    total = con.execute("SELECT COUNT(*) AS n FROM questions").fetchone()["n"]
    if total == 0:
        print("Quiz memory: empty — this is your first question.")
        return
    correct = con.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE judgment='correct'"
    ).fetchone()["n"]
    partial = con.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE judgment='partial'"
    ).fetchone()["n"]
    weakest = con.execute(
        """SELECT domain,
                  ROUND(1.0 * SUM(CASE WHEN judgment='correct' THEN 1 ELSE 0 END) / COUNT(*), 2) AS rate,
                  COUNT(*) AS asked
           FROM questions
           WHERE judgment IS NOT NULL AND judgment != 'skipped'
           GROUP BY domain
           HAVING asked >= 1
           ORDER BY rate ASC, asked DESC
           LIMIT 1"""
    ).fetchone()
    last = con.execute(
        "SELECT asked_at FROM questions ORDER BY id DESC LIMIT 1"
    ).fetchone()

    pct = int(round(100 * correct / total)) if total else 0
    parts = [f"Quiz memory: {total} answered", f"{correct} correct ({pct}%)"]
    if partial:
        parts.append(f"{partial} partial")
    if weakest and weakest["rate"] is not None and weakest["asked"] >= 2:
        parts.append(f"weakest: Domain {weakest['domain']}")
    if last:
        parts.append(f"last seen: {last['asked_at']}")
    print(" · ".join(parts))


def cmd_domains(_):
    """Plain-text markdown table of the 5 exam domains + per-domain question
    counts. Printed verbatim by SKILL.md — no JSON, no extra interpretation.

    Group by leading digit of stored domain string so both '1' and
    'Domain 1: Agentic...' aggregate the same way.
    """
    con = connect()
    rows = con.execute(
        """SELECT substr(domain, 1, 1) AS d,
                  COUNT(*) AS asked,
                  SUM(CASE WHEN judgment='correct'   THEN 1 ELSE 0 END) AS correct,
                  SUM(CASE WHEN judgment='partial'   THEN 1 ELSE 0 END) AS partial,
                  SUM(CASE WHEN judgment='incorrect' THEN 1 ELSE 0 END) AS incorrect
           FROM questions
           GROUP BY d"""
    ).fetchall()
    counts = {r["d"]: r for r in rows}

    print("| # | Domain | Weight | Asked | Correct | Partial | Incorrect | Pass rate |")
    print("|---|--------|-------:|------:|--------:|--------:|----------:|----------:|")
    tot_a = tot_c = tot_p = tot_i = 0
    for num, name, weight in DOMAINS:
        r = counts.get(num)
        a = r["asked"] if r else 0
        c = r["correct"] if r else 0
        p = r["partial"] if r else 0
        i = r["incorrect"] if r else 0
        rate = f"{int(round(100 * c / a))}%" if a else "—"
        print(f"| {num} | {name} | {weight}% | {a} | {c} | {p} | {i} | {rate} |")
        tot_a += a
        tot_c += c
        tot_p += p
        tot_i += i
    total_rate = f"{int(round(100 * tot_c / tot_a))}%" if tot_a else "—"
    print(
        f"| — | **Total** | 100% | **{tot_a}** | **{tot_c}** | "
        f"**{tot_p}** | **{tot_i}** | **{total_rate}** |"
    )

    canonical = {n for n, _, _ in DOMAINS}
    extras = [r for r in rows if r["d"] not in canonical]
    if extras:
        print()
        print("_Tracked outside the canonical 5 (likely test data):_")
        for r in extras:
            print(f"- domain `{r['d']}`: {r['asked']} asked")


def cmd_summary(args):
    """Recent questions with full coaching readback — for review mode."""
    con = connect()
    where, params = [], []
    if args.domain:
        where.append("domain = ?")
        params.append(args.domain)
    if args.judgment:
        where.append("judgment = ?")
        params.append(args.judgment)
    sql = (
        "SELECT id, asked_at, domain, task, topic, difficulty, judgment, "
        "question, expected_answer, user_answer, reasoning_notes, "
        "coaching_notes, related_context "
        "FROM questions"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(args.limit)
    rows = con.execute(sql, params).fetchall()
    emit([dict(r) for r in rows])


def cmd_start_session(args):
    con = connect()
    cur = con.execute(
        "INSERT INTO sessions(name, context_summary, notes) VALUES (?, ?, ?)",
        (args.name, args.context, args.notes),
    )
    con.commit()
    emit({"session_id": cur.lastrowid})


def cmd_log(args):
    """Silent on success: exit 0 with no stdout. Errors still surface via stderr
    + non-zero exit. The id confirmation isn't useful in the conversation; the
    user can verify with `stats` / `recent` / `summary` if they want.
    """
    con = connect()
    con.execute(
        """INSERT INTO questions
           (session_id, domain, task, topic, difficulty, question,
            expected_answer, user_answer, judgment, reasoning_notes,
            coaching_notes, related_context)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            args.session_id,
            args.domain,
            args.task,
            args.topic,
            args.difficulty,
            args.question,
            args.expected,
            args.answer,
            args.judgment,
            args.reasoning,
            args.coaching,
            args.context,
        ),
    )
    con.commit()


def cmd_stats(_):
    con = connect()
    rows = con.execute(
        """SELECT
              domain,
              COUNT(*) AS asked,
              SUM(CASE WHEN judgment='correct'   THEN 1 ELSE 0 END) AS correct,
              SUM(CASE WHEN judgment='partial'   THEN 1 ELSE 0 END) AS partial,
              SUM(CASE WHEN judgment='incorrect' THEN 1 ELSE 0 END) AS incorrect,
              SUM(CASE WHEN judgment='skipped'   THEN 1 ELSE 0 END) AS skipped
           FROM questions
           GROUP BY domain
           ORDER BY domain"""
    ).fetchall()
    total = con.execute("SELECT COUNT(*) AS n FROM questions").fetchone()["n"]
    correct = con.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE judgment='correct'"
    ).fetchone()["n"]
    partial = con.execute(
        "SELECT COUNT(*) AS n FROM questions WHERE judgment='partial'"
    ).fetchone()["n"]
    emit({
        "db": str(DB_PATH),
        "total_questions": total,
        "total_correct": correct,
        "total_partial": partial,
        "pass_rate_strict": (correct / total) if total else None,
        "pass_rate_lenient": ((correct + partial) / total) if total else None,
        "by_domain": [dict(r) for r in rows],
    })


def cmd_weakest(args):
    con = connect()
    rows = con.execute(
        """SELECT
              domain,
              COUNT(*) AS asked,
              ROUND(1.0 * SUM(CASE WHEN judgment='correct' THEN 1 ELSE 0 END) / COUNT(*), 3) AS rate
           FROM questions
           WHERE judgment IS NOT NULL AND judgment != 'skipped'
           GROUP BY domain
           HAVING asked >= ?
           ORDER BY rate ASC, asked DESC
           LIMIT ?""",
        (args.min_asked, args.limit),
    ).fetchall()
    emit([dict(r) for r in rows])


def cmd_recent(args):
    con = connect()
    rows = con.execute(
        """SELECT id, asked_at, domain, task, topic, difficulty, judgment,
                  substr(question, 1, 120) AS question_preview
           FROM questions
           ORDER BY id DESC
           LIMIT ?""",
        (args.n,),
    ).fetchall()
    emit([dict(r) for r in rows])


def cmd_show(args):
    con = connect()
    row = con.execute("SELECT * FROM questions WHERE id = ?", (args.id,)).fetchone()
    if not row:
        emit({"error": f"no question with id {args.id}"})
        sys.exit(1)
    emit(dict(row))


def cmd_export(args):
    con = connect()
    rows = con.execute("SELECT * FROM questions ORDER BY id").fetchall()
    out = [dict(r) for r in rows]
    Path(args.path).write_text(json.dumps(out, indent=2, default=str))
    emit({"exported": len(out), "path": args.path})


# ---------- argparse ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="quiz_db")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create DB + schema (auto-runs on other commands too)")
    sub.add_parser("banner", help="one-line plain-text memory signal for session start")
    sub.add_parser("domains", help="5-domain markdown table with per-domain answer counts")

    s = sub.add_parser("start-session", help="record a new quiz session")
    s.add_argument("--name")
    s.add_argument("--context")
    s.add_argument("--notes")

    s = sub.add_parser("log", help="log one question + judgment")
    s.add_argument("--session-id", type=int)
    s.add_argument("--domain", required=True,
                   help="e.g. '1' or 'Domain 1: Agentic Architecture'")
    s.add_argument("--task", help="task statement number, e.g. '1.3'")
    s.add_argument("--topic", help="short topic label")
    s.add_argument("--difficulty", default="medium",
                   choices=["easy", "medium", "hard", "exam"])
    s.add_argument("--question", required=True)
    s.add_argument("--expected", help="what a great answer touches on")
    s.add_argument("--answer", required=True, help="user's answer (verbatim)")
    s.add_argument("--judgment", required=True,
                   choices=["correct", "partial", "incorrect", "skipped"])
    s.add_argument("--reasoning", help="coach's notes on user's reasoning quality")
    s.add_argument("--coaching", help="explanation given back to the user")
    s.add_argument("--context", help="conversation snippet that informed the question")

    sub.add_parser("stats", help="aggregate counts + pass rates")

    s = sub.add_parser("weakest", help="weakest domains (for theme picking)")
    s.add_argument("--limit", type=int, default=3)
    s.add_argument("--min-asked", type=int, default=1)

    s = sub.add_parser("summary",
                       help="recent questions with full coaching readback (review mode)")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--domain", help="filter by domain")
    s.add_argument("--judgment",
                   choices=["correct", "partial", "incorrect", "skipped"],
                   help="filter by judgment")

    s = sub.add_parser("recent", help="last N questions")
    s.add_argument("n", type=int, nargs="?", default=10)

    s = sub.add_parser("show", help="full detail of one question")
    s.add_argument("id", type=int)

    s = sub.add_parser("export", help="dump all questions as JSON")
    s.add_argument("path")

    return p


def main() -> None:
    args = build_parser().parse_args()
    handlers = {
        "init": cmd_init,
        "banner": cmd_banner,
        "domains": cmd_domains,
        "start-session": cmd_start_session,
        "log": cmd_log,
        "stats": cmd_stats,
        "weakest": cmd_weakest,
        "summary": cmd_summary,
        "recent": cmd_recent,
        "show": cmd_show,
        "export": cmd_export,
    }
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
