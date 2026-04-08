"""SkillForge Database — SQLite persistence for candidates, analyses, assessments, and learning plans."""

import sqlite3
import json
import os
import logging

DB_PATH = os.getenv("DB_PATH", "/tmp/skillforge.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            skills TEXT NOT NULL,
            experience_summary TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            jd_text TEXT NOT NULL,
            role_title TEXT DEFAULT '',
            required_skills TEXT DEFAULT '{}',
            gap_analysis TEXT DEFAULT '{}',
            market_research TEXT DEFAULT '{}',
            readiness_score REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            candidate_id INTEGER NOT NULL,
            questions TEXT DEFAULT '[]',
            correct_answers TEXT DEFAULT '[]',
            overall_score REAL DEFAULT 0.0,
            difficulty_level TEXT DEFAULT 'medium',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (analysis_id) REFERENCES analyses(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        );

        CREATE TABLE IF NOT EXISTS learning_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            analysis_id INTEGER,
            assessment_id INTEGER,
            plan TEXT DEFAULT '{}',
            timeline_weeks INTEGER DEFAULT 4,
            resources TEXT DEFAULT '[]',
            milestones TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (analysis_id) REFERENCES analyses(id),
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        );
    """)
    conn.commit()
    conn.close()
    logging.info("[SkillForge DB] Tables initialized")


# --- CRUD Operations ---

def insert_candidate(name: str, skills: str, email: str = "", experience: str = "") -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO candidates (name, email, skills, experience_summary) VALUES (?, ?, ?, ?)",
        (name, email, skills, experience)
    )
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"[DB] Candidate saved: id={candidate_id}, name={name}")
    return candidate_id


def insert_analysis(candidate_id: int, jd_text: str, role_title: str,
                    required_skills: str, gap_analysis: str,
                    market_research: str, readiness_score: float) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO analyses
           (candidate_id, jd_text, role_title, required_skills, gap_analysis, market_research, readiness_score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (candidate_id, jd_text, role_title, required_skills, gap_analysis, market_research, readiness_score)
    )
    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"[DB] Analysis saved: id={analysis_id}")
    return analysis_id


def insert_assessment(analysis_id: int, candidate_id: int, questions: str,
                      correct_answers: str, overall_score: float,
                      difficulty: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO assessments
           (analysis_id, candidate_id, questions, correct_answers, overall_score, difficulty_level)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (analysis_id, candidate_id, questions, correct_answers, overall_score, difficulty)
    )
    assessment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"[DB] Assessment saved: id={assessment_id}")
    return assessment_id


def insert_learning_plan(candidate_id: int, analysis_id: int, assessment_id: int,
                         plan: str, timeline_weeks: int, resources: str,
                         milestones: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO learning_plans
           (candidate_id, analysis_id, assessment_id, plan, timeline_weeks, resources, milestones)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (candidate_id, analysis_id, assessment_id, plan, timeline_weeks, resources, milestones)
    )
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"[DB] Learning plan saved: id={plan_id}")
    return plan_id


def get_candidate(candidate_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_latest_analysis(candidate_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM analyses WHERE candidate_id = ? ORDER BY created_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_latest_assessment(candidate_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM assessments WHERE candidate_id = ? ORDER BY created_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_latest_plan(candidate_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM learning_plans WHERE candidate_id = ? ORDER BY created_at DESC LIMIT 1",
        (candidate_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_all_candidates() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT id, name, skills, created_at FROM candidates ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_candidate_history(candidate_id: int) -> dict:
    conn = get_connection()
    candidate = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    analyses = conn.execute(
        "SELECT * FROM analyses WHERE candidate_id = ? ORDER BY created_at", (candidate_id,)
    ).fetchall()
    assessments = conn.execute(
        "SELECT * FROM assessments WHERE candidate_id = ? ORDER BY created_at", (candidate_id,)
    ).fetchall()
    plans = conn.execute(
        "SELECT * FROM learning_plans WHERE candidate_id = ? ORDER BY created_at", (candidate_id,)
    ).fetchall()
    conn.close()

    return {
        "candidate": dict(candidate) if candidate else {},
        "analyses": [dict(r) for r in analyses],
        "assessments": [dict(r) for r in assessments],
        "learning_plans": [dict(r) for r in plans],
        "total_assessments": len(assessments),
        "score_progression": [dict(r).get("overall_score", 0) for r in assessments]
    }
