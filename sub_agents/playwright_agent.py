from google.adk.agents import LlmAgent    
from google.adk.agents import Agent   
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
from dotenv import load_dotenv
import os

load_dotenv('../.env')

MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT', 8931)
async def get_playwright_agent():

    playwright_tools, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")
            # connection_params=StdioServerParameters(
            #     command='python',
            #     args=["-y",    # Arguments for the command
            #         "@playwright/mcp@latest",
            #         # "--vision",
            #     ],
            # ) 
    )
    print(f"Fetched {len(playwright_tools)} tools from Playwright MCP server.")
    slack_agent = Agent(
        model="gemini-2.0-flash",
        name="playwright_agent", # Keep original name
        description="Handle Slack-related tasks like sending messages using tools provided.",
        instruction="You are the Slack Agent. Your ONLY task is interacts with Slack workspace using tools provided. Do not perform any other actions.",
        tools=playwright_tools,
    )

    return slack_agent