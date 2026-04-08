"""SkillForge Agents — Multi-agent career intelligence pipeline using Google ADK."""

import logging
import os
import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools import google_search

from . import prompt as prompts
from .tools import (
    save_input_to_state,
    save_candidate_to_db,
    save_research_to_state,
    save_analysis_to_state,
    save_analysis_to_db,
    save_assessment_to_state,
    save_assessment_to_db,
    save_plan_to_state,
    save_plan_to_db,
)
from .db import init_db

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL", "gemini-2.0-flash")

init_db()


# Research Agent: Analyzes job descriptions and researches market skill requirements using web search.
research_agent = Agent(
    name="research_agent",
    model=model_name,
    description="Analyzes job descriptions and researches market skill requirements using web search.",
    instruction=prompts.RESEARCH_AGENT_INSTRUCTION,
    tools=[save_research_to_state, google_search],
)

# Skill Analyzer: Compares required skills against candidate profile to identify gaps and calculate readiness.
skill_analyzer = Agent(
    name="skill_analyzer",
    model=model_name,
    description="Compares required skills against candidate profile to identify gaps and calculate readiness.",
    instruction=prompts.SKILL_ANALYZER_INSTRUCTION,
    tools=[save_analysis_to_state, save_analysis_to_db],
)

# Assessment Agent: Generates adaptive skill assessment questions targeting identified gaps.
assessment_agent = Agent(
    name="assessment_agent",
    model=model_name,
    description="Generates adaptive skill assessment questions targeting identified gaps.",
    instruction=prompts.ASSESSMENT_AGENT_INSTRUCTION,
    tools=[save_assessment_to_state, save_assessment_to_db],
)

# Learning Planner: Creates personalized, time-bound learning plans with real resources and milestones.
learning_planner = Agent(
    name="learning_planner",
    model=model_name,
    description="Creates personalized, time-bound learning plans with real resources and milestones.",
    instruction=prompts.LEARNING_PLANNER_INSTRUCTION,
    tools=[save_plan_to_state, save_plan_to_db, google_search],
)

analysis_pipeline = SequentialAgent(
    name="analysis_pipeline",
    description="Runs the full SkillForge analysis: Research -> Gap Analysis -> Assessment -> Learning Plan.",
    agents=[research_agent, skill_analyzer, assessment_agent, learning_planner],
)


# Root Agent: Orchestrates the entire multi-agent pipeline, starting with collecting job description and candidate skills, then coordinating the analysis process.
root_agent = Agent(
    name="skillforge_orchestrator",
    model=model_name,
    description="SkillForge entry point — collects job description and candidate skills, then orchestrates the multi-agent analysis pipeline.",
    instruction=prompts.ORCHESTRATOR_INSTRUCTION,
    tools=[save_input_to_state, save_candidate_to_db],
    sub_agents=[analysis_pipeline],
)
