"""SkillForge Tools — Simplified custom tools (one per agent)."""

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
    # Save to state
    tool_context.state["JD_TEXT"] = jd_text
    tool_context.state["CANDIDATE_NAME"] = candidate_name
    tool_context.state["CANDIDATE_SKILLS"] = candidate_skills

    # Save to database
    candidate_id = db.insert_candidate(
        name=candidate_name,
        skills=candidate_skills,
    )
    tool_context.state["CANDIDATE_ID"] = candidate_id

    logging.info(f"[Input] Saved {candidate_name}, ID: {candidate_id}")

    return {
        "status": "success",
        "candidate_id": candidate_id,
        "message": f"Candidate profile for {candidate_name} has been successfully persisted to the database with ID: {candidate_id}."
    }


# ===== TOOL 2: RESEARCH ROLE =====
# Note: research_agent uses google_search directly, no custom tool needed

def save_research(
    tool_context: ToolContext,
    role_title: str,
    required_skills: str,
    market_insights: str
) -> dict:
    """Saves market research findings to state.

    Args:
        role_title: The target role title (e.g., "Senior ML Engineer").
        required_skills: JSON string of required skills categorized by type.
        market_insights: Market intelligence summary.

    Returns:
        Confirmation.
    """
    research = {
        "role_title": role_title,
        "required_skills": required_skills,
        "market_insights": market_insights
    }
    tool_context.state["RESEARCH_RESULTS"] = json.dumps(research)
    tool_context.state["ROLE_TITLE"] = role_title

    logging.info(f"[Research] Saved research for {role_title}")

    return {
        "status": "success",
        "role_title": role_title
    }


# ===== TOOL 3: ANALYZE SKILLS =====

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
    # Get data from state
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    jd_text = tool_context.state.get("JD_TEXT", "")
    role_title = tool_context.state.get("ROLE_TITLE", "")
    research_results = tool_context.state.get("RESEARCH_RESULTS", "{}")

    # Save to state
    analysis_data = {
        "gap_analysis": gap_analysis,
        "readiness_score": readiness_score,
        "priority_gaps": priority_gaps
    }
    tool_context.state["GAP_ANALYSIS"] = json.dumps(analysis_data)
    tool_context.state["READINESS_SCORE"] = readiness_score

    # Save to database
    analysis_id = db.insert_analysis(
        candidate_id=int(candidate_id),
        jd_text=jd_text,
        role_title=role_title,
        required_skills="",
        gap_analysis=gap_analysis,
        market_research=research_results,
        readiness_score=float(readiness_score)
    )
    tool_context.state["ANALYSIS_ID"] = analysis_id

    logging.info(f"[Analyzer] Analysis saved, ID: {analysis_id}, Score: {readiness_score}%")

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "readiness_score": readiness_score,
        "message": f"Skill gap analysis completed. Readiness score: {readiness_score}%"
    }


# ===== TOOL 4: CREATE PLAN =====

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
    # Get data from state
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    analysis_id = tool_context.state.get("ANALYSIS_ID", 0)

    # Save assessment
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

    # Save learning plan
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

    logging.info(f"[Planner] Plan saved, ID: {plan_id}, Duration: {timeline_weeks} weeks")

    return {
        "status": "success",
        "assessment_id": assessment_id,
        "plan_id": plan_id,
        "timeline_weeks": timeline_weeks,
        "message": f"Assessment and {timeline_weeks}-week learning plan created successfully!"
    }
