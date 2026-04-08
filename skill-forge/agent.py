"""SkillForge Agents — Simplified multi-agent career intelligence pipeline."""

import logging
import os
import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools import google_search

from . import prompt
from .tools import (
    process_input,
    analyze_skills,
    create_plan,
)
from .db import init_db

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL", "gemini-2.0-flash")

init_db()


# ===== CORE AGENTS (one tool each) =====

# Input Agent: Collects and persists user input
input_agent = Agent(
    name="input_agent",
    model=model_name,
    description="Collects job description and candidate profile, saves to state and database.",
    instruction=prompt.INPUT_AGENT_INSTRUCTION,
    tools=[process_input]
)

# Research Agent: Market intelligence with google_search
research_agent = Agent(
    name="research_agent",
    model=model_name,
    description="Researches market requirements and role expectations using web search.",
    instruction=prompt.RESEARCH_AGENT_INSTRUCTION,
    tools=[google_search]
)

# Analyzer Agent: Performs skill gap analysis
analyzer_agent = Agent(
    name="analyzer_agent",
    model=model_name,
    description="Analyzes skill gaps, calculates readiness score, persists analysis.",
    instruction=prompt.ANALYZER_AGENT_INSTRUCTION,
    tools=[analyze_skills]
)

# Planner Agent: Creates assessment and learning plan (with search capability)
planner_agent = Agent(
    name="planner_agent",
    model=model_name,
    description="Generates adaptive assessment and personalized learning roadmap.",
    instruction=prompt.PLANNER_AGENT_INSTRUCTION,
    tools=[google_search, create_plan]
)


# ===== PIPELINE =====

# Main Pipeline: Runs all 4 agents sequentially
main_pipeline = SequentialAgent(
    name="main_pipeline",
    description="Runs the full SkillForge workflow: Input → Research → Analysis → Planning",
    sub_agents=[input_agent, research_agent, analyzer_agent, planner_agent]
)


# ===== ROOT AGENT =====

# Root Agent: Entry point that delegates to main pipeline
root_agent = Agent(
    name="skillforge_orchestrator",
    model=model_name,
    description="SkillForge entry point — collects job description and candidate skills, then orchestrates analysis.",
    instruction=prompt.ORCHESTRATOR_INSTRUCTION,
    sub_agents=[main_pipeline]
)
