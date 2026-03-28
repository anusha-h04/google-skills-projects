import logging
import os
import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

# --- Setup Logging and Environment ---

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

from . import prompt

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL")


# Greet user and save their prompt

def add_prompt_to_state(
    tool_context: ToolContext, prompt: str
) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}


concept_map_generator = Agent(
    name="concept_map_generator",
    model=model_name,
    description="Analyzes text and generates visual concept maps as Mermaid diagrams.",
    instruction=f"""
    1. Retrieve user's text: tool_context.state.get("PROMPT")
    2. Analyze and extract concepts/relationships
    3. {prompt.SYSTEM_PROMPT}
    4. Return the Mermaid diagram - it will render visually in the ADK UI
    """,
    tools=[]
)


root_agent = Agent(
    name="greeter",
    model=model_name,
    description="Entry point that gathers and validates user input for concept mapping.",
    instruction="""
    Greet the user and ask for text to analyze (article, paragraph, topic explanation).

    **Validate input:**
    - Too short (< 20 words)? Ask for more detail
    - Single word/unclear? Confirm: "Need more text or just this?"
    - Question vs. text? Clarify intent
    - URL/file? Request actual text content

    **Once valid (20+ words):**
    - Use 'add_prompt_to_state' tool to save text
    - Transfer to 'concept_map_generator' agent

    Be helpful and ensure quality input before proceeding.
    """,
    tools=[add_prompt_to_state],
    sub_agents=[concept_map_generator]
)