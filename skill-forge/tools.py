"""SkillForge Tools — Custom tools for agent pipeline."""

import json
import logging
from google.adk.tools.tool_context import ToolContext
from . import db


# ===== TOOL 1: PROCESS INPUT =====

def process_input(
    tool_context: ToolContext,
    jd_text: str,
    candidate_name: str,
    candidate_skills: str
) -> dict:
    """Saves job description and candidate profile to state and database.

    Args:
        jd_text: The full job description text.
        candidate_name: The candidate's name.
        candidate_skills: Comma-separated skills and experience.

    Returns:
        Confirmation with candidate_id.
    """
    tool_context.state["JD_TEXT"] = jd_text
    tool_context.state["CANDIDATE_NAME"] = candidate_name
    tool_context.state["CANDIDATE_SKILLS"] = candidate_skills

    candidate_id = db.insert_candidate(
        name=candidate_name,
        skills=candidate_skills,
    )
    tool_context.state["CANDIDATE_ID"] = candidate_id

    logging.info(f"[Input] Saved {candidate_name}, ID: {candidate_id}")

    return {
        "status": "success",
        "candidate_id": candidate_id,
        "message": f"Candidate profile saved with ID: {candidate_id}."
    }


# ===== TOOL 2: ANALYZE SKILLS =====

def analyze_skills(
    tool_context: ToolContext,
    gap_analysis: str,
    readiness_score: float,
    priority_gaps: str
) -> dict:
    """Analyzes skill gaps and saves to state and database.

    Args:
        gap_analysis: JSON string of skill-by-skill assessment.
        readiness_score: Overall readiness percentage (0-100).
        priority_gaps: JSON string of top gaps to address.

    Returns:
        Confirmation with analysis_id and score.
    """
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    jd_text = tool_context.state.get("JD_TEXT", "")

    analysis_data = {
        "gap_analysis": gap_analysis,
        "readiness_score": readiness_score,
        "priority_gaps": priority_gaps
    }
    tool_context.state["GAP_ANALYSIS"] = json.dumps(analysis_data)
    tool_context.state["READINESS_SCORE"] = readiness_score

    analysis_id = db.insert_analysis(
        candidate_id=int(candidate_id),
        jd_text=jd_text,
        role_title="",
        required_skills="",
        gap_analysis=gap_analysis,
        market_research="",
        readiness_score=float(readiness_score)
    )
    tool_context.state["ANALYSIS_ID"] = analysis_id

    logging.info(f"[Analyzer] Analysis ID: {analysis_id}, Score: {readiness_score}%")

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "readiness_score": readiness_score,
        "message": f"Gap analysis completed. Readiness: {readiness_score}%"
    }


# ===== TOOL 3: CREATE PLAN =====

def create_plan(
    tool_context: ToolContext,
    assessment_questions: str,
    learning_plan: str,
    timeline_weeks: int,
    resources: str
) -> dict:
    """Generates assessment and learning plan, saves to state and database.

    Args:
        assessment_questions: JSON string of adaptive questions.
        learning_plan: JSON string with week-by-week learning roadmap.
        timeline_weeks: Total number of weeks (4-12).
        resources: JSON string of learning resources with URLs.

    Returns:
        Confirmation with assessment_id and plan_id.
    """
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    analysis_id = tool_context.state.get("ANALYSIS_ID", 0)

    tool_context.state["ASSESSMENT"] = assessment_questions
    assessment_id = db.insert_assessment(
        analysis_id=int(analysis_id),
        candidate_id=int(candidate_id),
        questions=assessment_questions,
        correct_answers="[]",
        overall_score=0.0,
        difficulty="adaptive"
    )
    tool_context.state["ASSESSMENT_ID"] = assessment_id

    tool_context.state["LEARNING_PLAN"] = learning_plan
    tool_context.state["PLAN_TIMELINE"] = timeline_weeks
    plan_id = db.insert_learning_plan(
        candidate_id=int(candidate_id),
        analysis_id=int(analysis_id),
        assessment_id=assessment_id,
        plan=learning_plan,
        timeline_weeks=int(timeline_weeks),
        resources=resources,
        milestones="[]"
    )
    tool_context.state["PLAN_ID"] = plan_id

    logging.info(f"[Planner] Plan ID: {plan_id}, Duration: {timeline_weeks} weeks")

    return {
        "status": "success",
        "assessment_id": assessment_id,
        "plan_id": plan_id,
        "timeline_weeks": timeline_weeks,
        "message": f"Assessment and {timeline_weeks}-week plan created."
    }
