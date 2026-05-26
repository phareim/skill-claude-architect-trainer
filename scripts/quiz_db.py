#!/usr/bin/env python3
"""SQLite store for the claude-quiz skill.

Subcommands:
  init                          create DB + schema if missing
  start-session                 record a new quiz session
  log                           log one question + judgment
  stats                         aggregate counts + per-domain pass rate
  weakest                       3 weakest domains by pass rate (for theme picking)
  recent [N]                    last N questions
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


def cmd_start_session(args):
    con = connect()
    cur = con.execute(
        "INSERT INTO sessions(name, context_summary, notes) VALUES (?, ?, ?)",
        (args.name, args.context, args.notes),
    )
    con.commit()
    emit({"session_id": cur.lastrowid})


def cmd_log(args):
    con = connect()
    cur = con.execute(
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
    emit({"question_id": cur.lastrowid, "db": str(DB_PATH)})


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

    sub.add_parser("init", help="create DB + schema if missing")

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
        "start-session": cmd_start_session,
        "log": cmd_log,
        "stats": cmd_stats,
        "weakest": cmd_weakest,
        "recent": cmd_recent,
        "show": cmd_show,
        "export": cmd_export,
    }
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
