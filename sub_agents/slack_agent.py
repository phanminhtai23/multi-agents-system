from google.adk.agents import LlmAgent    
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
import os
SLACK_MCP_URL = os.getenv('SLACK_MCP_URL')

async def get_slack_agent():

    tools1, exit_stack = await MCPToolset.from_server(
            # connection_params=SseServerParams(url="http://localhost:8931/sse")
            connection_params=SseServerParams(url=SLACK_MCP_URL)
    )
    print(f"Fetched {len(tools1)} tools from Slack MCP server.")
    slack_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="slack_agent", # Keep original name
        description="Handle Slack-related tasks like sending messages using tools provided.",
        instruction="You are the Slack Agent. Your ONLY task is interacts with Slack workspace using tools provided. Do not perform any other actions.",
        tools=tools1,
    )

    return slack_agent