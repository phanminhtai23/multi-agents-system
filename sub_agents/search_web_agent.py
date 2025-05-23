from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.tools import google_search

def get_search_web_agent():
    search_web_agent = Agent(
            model="gemini-2.0-flash",
            name="search_web_agent", # Keep original name for consistency
            instruction="You are Search Web Agent, you can use 'google_search' tool to answer questions about realtime data",
            description="Handles questions about searching the web or realtime data using 'google_search' tool",
            tools=[google_search],
        )
    return search_web_agent