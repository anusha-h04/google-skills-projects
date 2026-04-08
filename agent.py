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
    tools=[process_input],
)

# Search Sub-Agent: Performs web searches
search_sub_agent = Agent(
    name="search_sub_agent",
    model=model_name,
    description="Performs web searches for market intelligence.",
    instruction="You are a search specialist. Use google_search to find current market data, required skills, salary ranges, and technology trends for the role described in state.",
    tools=[google_search],
)

# Research Agent: Market intelligence coordinator (uses search sub-agent)
research_agent = Agent(
    name="research_agent",
    model=model_name,
    description="Researches market requirements and role expectations using web search.",
    instruction=prompt.RESEARCH_AGENT_INSTRUCTION,
    sub_agents=[search_sub_agent],
)

# Analyzer Agent: Performs skill gap analysis
analyzer_agent = Agent(
    name="analyzer_agent",
    model=model_name,
    description="Analyzes skill gaps, calculates readiness score, persists analysis.",
    instruction=prompt.ANALYZER_AGENT_INSTRUCTION,
    tools=[analyze_skills],
)

# Search Sub-Agent for Planner: Finds learning resources
resource_search_agent = Agent(
    name="resource_search_agent",
    model=model_name,
    description="Finds learning resources, courses, and tutorials via web search.",
    instruction="You are a learning resource specialist. Use google_search to find free courses, tutorials, documentation, and practice projects for the skills identified in the gap analysis. Search for 3-5 high-quality resources per skill gap.",
    tools=[google_search],
)

# Plan Saver Agent: Generates assessment and saves plan
plan_saver_agent = Agent(
    name="plan_saver_agent",
    model=model_name,
    description="Generates adaptive assessment and personalized learning roadmap, saves to database.",
    instruction=prompt.PLANNER_AGENT_INSTRUCTION,
    tools=[create_plan],
)

# Planner Pipeline: Sequential execution of resource search then plan creation
planner_pipeline = SequentialAgent(
    name="planner_pipeline",
    description="Find learning resources, then generate assessment and learning plan.",
    sub_agents=[resource_search_agent, plan_saver_agent],
)


# ===== PIPELINE =====

# Main Pipeline: Runs all 4 stages sequentially
main_pipeline = SequentialAgent(
    name="main_pipeline",
    description="Runs the full SkillForge workflow: Input → Research → Analysis → Planning",
    sub_agents=[input_agent, research_agent, analyzer_agent, planner_pipeline],
)


# ===== ROOT AGENT =====

# Root Agent: Entry point that delegates to main pipeline
root_agent = Agent(
    name="skillforge_orchestrator",
    model=model_name,
    description="SkillForge entry point — collects job description and candidate skills, then orchestrates analysis.",
    instruction=prompt.ORCHESTRATOR_INSTRUCTION,
    sub_agents=[main_pipeline],
)
