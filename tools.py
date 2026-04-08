"""SkillForge Tools — Functions available to agents via Google ADK ToolContext."""

import json
import logging
from google.adk.tools.tool_context import ToolContext
from . import db

def save_input_to_state(
    tool_context: ToolContext,
    jd_text: str,
    candidate_name: str,
    candidate_skills: str
) -> dict:
    """Saves the job description and candidate information to shared state for the analysis pipeline.

    Args:
        jd_text: The full job description text or role title to analyze.
        candidate_name: The candidate's full name.
        candidate_skills: Comma-separated list of the candidate's current skills and experience.

    Returns:
        Confirmation with status.
    """
    tool_context.state["JD_TEXT"] = jd_text
    tool_context.state["CANDIDATE_NAME"] = candidate_name
    tool_context.state["CANDIDATE_SKILLS"] = candidate_skills
    logging.info(f"[State] Input saved for {candidate_name} — JD: {len(jd_text)} chars")
    return {
        "status": "success",
        "message": f"Saved input for {candidate_name}. JD length: {len(jd_text)} chars."
    }


def save_candidate_to_db(
    tool_context: ToolContext,
    name: str,
    skills: str,
    email: str = "",
    experience_summary: str = ""
) -> dict:
    """Persists a candidate profile to the database for long-term tracking.

    Args:
        name: The candidate's full name.
        skills: Comma-separated list of skills.
        email: Optional email address.
        experience_summary: Optional brief experience summary.

    Returns:
        Dict with candidate_id.
    """
    candidate_id = db.insert_candidate(name, skills, email, experience_summary)
    tool_context.state["CANDIDATE_ID"] = candidate_id
    logging.info(f"[DB] Candidate persisted: id={candidate_id}")
    return {"status": "success", "candidate_id": candidate_id}

def save_research_to_state(
    tool_context: ToolContext,
    role_title: str,
    required_skills_json: str,
    market_insights: str,
    skill_rankings_json: str
) -> dict:
    """Saves the research agent's market intelligence findings to shared state.

    Args:
        role_title: The identified role title and level (e.g. 'Senior ML Engineer').
        required_skills_json: JSON string of categorized skills. Example: {"technical": ["Python", "TensorFlow"], "soft": ["Communication"], "domain": ["ML Systems"]}
        market_insights: Summary of market research — salary, demand, and trends.
        skill_rankings_json: JSON string ranking each skill. Example: [{"skill": "Python", "importance": "CRITICAL"}, {"skill": "Docker", "importance": "IMPORTANT"}]

    Returns:
        Confirmation with status.
    """
    research = {
        "role_title": role_title,
        "required_skills": required_skills_json,
        "market_insights": market_insights,
        "skill_rankings": skill_rankings_json
    }
    tool_context.state["RESEARCH_RESULTS"] = json.dumps(research)
    tool_context.state["ROLE_TITLE"] = role_title
    logging.info(f"[State] Research saved — role: {role_title}")
    return {"status": "success", "role_title": role_title}

def save_analysis_to_state(
    tool_context: ToolContext,
    gap_analysis_json: str,
    readiness_score: float,
    priority_gaps_json: str,
    strengths_json: str
) -> dict:
    """Saves the skill gap analysis results to shared state.

    Args:
        gap_analysis_json: JSON string with per-skill assessment. Example: [{"skill": "Python", "status": "STRONG", "notes": "5 years experience"}, {"skill": "Kubernetes", "status": "GAP", "notes": "No experience"}]
        readiness_score: Overall readiness percentage (0.0 to 100.0).
        priority_gaps_json: JSON string of top gaps to address. Example: [{"skill": "Kubernetes", "importance": "CRITICAL", "learnability": "medium"}]
        strengths_json: JSON string of candidate strengths. Example: ["Python", "SQL", "Machine Learning"]

    Returns:
        Confirmation with readiness score.
    """
    analysis = {
        "gap_analysis": gap_analysis_json,
        "readiness_score": readiness_score,
        "priority_gaps": priority_gaps_json,
        "strengths": strengths_json
    }
    tool_context.state["GAP_ANALYSIS"] = json.dumps(analysis)
    tool_context.state["READINESS_SCORE"] = readiness_score
    logging.info(f"[State] Gap analysis saved — readiness: {readiness_score}%")
    return {"status": "success", "readiness_score": readiness_score}


def save_analysis_to_db(tool_context: ToolContext) -> dict:
    """Persists the current gap analysis from state to the database. No arguments needed — reads everything from shared state.

    Returns:
        Dict with analysis_id.
    """
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    jd_text = tool_context.state.get("JD_TEXT", "")
    role_title = tool_context.state.get("ROLE_TITLE", "")
    research = tool_context.state.get("RESEARCH_RESULTS", "{}")
    gap_analysis = tool_context.state.get("GAP_ANALYSIS", "{}")
    readiness_score = tool_context.state.get("READINESS_SCORE", 0.0)

    try:
        research_data = json.loads(research) if isinstance(research, str) else research
        required_skills = research_data.get("required_skills", "{}")
        market_research = research_data.get("market_insights", "")
    except (json.JSONDecodeError, AttributeError):
        required_skills = "{}"
        market_research = ""

    analysis_id = db.insert_analysis(
        candidate_id=int(candidate_id),
        jd_text=jd_text,
        role_title=role_title,
        required_skills=str(required_skills),
        gap_analysis=str(gap_analysis),
        market_research=str(market_research),
        readiness_score=float(readiness_score)
    )
    tool_context.state["ANALYSIS_ID"] = analysis_id
    logging.info(f"[DB] Analysis persisted: id={analysis_id}")
    return {"status": "success", "analysis_id": analysis_id}


def save_assessment_to_state(
    tool_context: ToolContext,
    questions_json: str,
    correct_answers_json: str,
    difficulty_level: str = "mixed"
) -> dict:
    """Saves the generated assessment questions and hidden answers to shared state.

    Args:
        questions_json: JSON string of questions shown to the user. Example: [{"number": 1, "skill": "Kubernetes", "difficulty": "Basic", "type": "MCQ", "question": "What is a Pod?", "options": ["A", "B", "C", "D"]}]
        correct_answers_json: JSON string of correct answers — hidden from user. Example: [{"number": 1, "answer": "A", "explanation": "A Pod is the smallest deployable unit"}]
        difficulty_level: Overall difficulty — basic, intermediate, advanced, or mixed.

    Returns:
        Confirmation with question count.
    """
    tool_context.state["ASSESSMENT"] = questions_json
    tool_context.state["CORRECT_ANSWERS"] = correct_answers_json
    tool_context.state["ASSESSMENT_DIFFICULTY"] = difficulty_level

    try:
        count = len(json.loads(questions_json))
    except (json.JSONDecodeError, TypeError):
        count = 0

    logging.info(f"[State] Assessment saved — {count} questions, difficulty: {difficulty_level}")
    return {"status": "success", "question_count": count}


def save_assessment_to_db(tool_context: ToolContext) -> dict:
    """Persists the current assessment from state to the database. No arguments needed — reads from shared state.

    Returns:
        Dict with assessment_id.
    """
    analysis_id = tool_context.state.get("ANALYSIS_ID", 0)
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    questions = tool_context.state.get("ASSESSMENT", "[]")
    correct_answers = tool_context.state.get("CORRECT_ANSWERS", "[]")
    difficulty = tool_context.state.get("ASSESSMENT_DIFFICULTY", "mixed")

    assessment_id = db.insert_assessment(
        analysis_id=int(analysis_id),
        candidate_id=int(candidate_id),
        questions=str(questions),
        correct_answers=str(correct_answers),
        overall_score=0.0,
        difficulty=difficulty
    )
    tool_context.state["ASSESSMENT_ID"] = assessment_id
    logging.info(f"[DB] Assessment persisted: id={assessment_id}")
    return {"status": "success", "assessment_id": assessment_id}


def save_plan_to_state(
    tool_context: ToolContext,
    plan_json: str,
    timeline_weeks: int,
    milestones_json: str,
    resources_json: str
) -> dict:
    """Saves the personalized learning plan to shared state.

    Args:
        plan_json: JSON string with week-by-week plan. Example: [{"week": 1, "focus": "Kubernetes Basics", "tasks": ["Complete K8s tutorial", "Deploy first pod"], "resources": ["https://..."], "hours_per_day": 1.5}]
        timeline_weeks: Total number of weeks for the plan (4-12).
        milestones_json: JSON string of key milestones. Example: [{"week": 4, "milestone": "Deploy app to K8s cluster", "criteria": "Working deployment with 3 replicas"}]
        resources_json: JSON string of all learning resources. Example: [{"name": "K8s Official Tutorial", "url": "https://...", "type": "tutorial", "skill": "Kubernetes"}]

    Returns:
        Confirmation with timeline.
    """
    tool_context.state["LEARNING_PLAN"] = plan_json
    tool_context.state["PLAN_TIMELINE"] = timeline_weeks
    tool_context.state["PLAN_MILESTONES"] = milestones_json
    tool_context.state["PLAN_RESOURCES"] = resources_json
    logging.info(f"[State] Learning plan saved — {timeline_weeks} weeks")
    return {"status": "success", "timeline_weeks": timeline_weeks}


def save_plan_to_db(tool_context: ToolContext) -> dict:
    """Persists the current learning plan from state to the database. No arguments needed — reads from shared state.

    Returns:
        Dict with plan_id.
    """
    candidate_id = tool_context.state.get("CANDIDATE_ID", 0)
    analysis_id = tool_context.state.get("ANALYSIS_ID", 0)
    assessment_id = tool_context.state.get("ASSESSMENT_ID", 0)
    plan = tool_context.state.get("LEARNING_PLAN", "{}")
    timeline = tool_context.state.get("PLAN_TIMELINE", 4)
    resources = tool_context.state.get("PLAN_RESOURCES", "[]")
    milestones = tool_context.state.get("PLAN_MILESTONES", "[]")

    plan_id = db.insert_learning_plan(
        candidate_id=int(candidate_id),
        analysis_id=int(analysis_id),
        assessment_id=int(assessment_id),
        plan=str(plan),
        timeline_weeks=int(timeline),
        resources=str(resources),
        milestones=str(milestones)
    )
    tool_context.state["PLAN_ID"] = plan_id
    logging.info(f"[DB] Learning plan persisted: id={plan_id}")
    return {"status": "success", "plan_id": plan_id}
