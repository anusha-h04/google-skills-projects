"""Resume Scorer - ADK Web Application"""

from root_agent import root_agent


if __name__ == "__main__":
    # For local testing
    test_prompt = "Analyze this resume: John Doe, 5 years Python experience, built web apps."
    print("Testing agent...")
    print(root_agent(test_prompt))