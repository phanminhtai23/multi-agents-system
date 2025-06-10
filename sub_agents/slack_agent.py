from google.adk.agents import LlmAgent    
from google.adk.agents import Agent    
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv('../.env')
SLACK_MCP_URL = os.getenv('SLACK_MCP_URL', "https://mcp.pipedream.net/e23c22c5-a414-47db-907f-cb0ca7690055/slack")
MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT')

async def get_slack_agent():

    # print(f"SLACK_MCP_URL: {SLACK_MCP_URL}")

    tools1, exit_stack = await MCPToolset.from_server(
            # connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")
            connection_params=SseServerParams(url=SLACK_MCP_URL)
            # connection_params=StdioServerParameters(
            #     command= "npx",
            #     args = [
            #         "-y",
            #         "supergateway",
            #         "--sse",
            #         "https://mcp.pipedream.net/e23c22c5-a414-47db-907f-cb0ca7690055/slack"
            #     ]
            # )
    )
    print(f"Fetched {len(tools1)} tools from Slack MCP server.")
    slack_agent = Agent(
        model="gemini-2.0-flash-exp",
        name="slack_agent", # Keep original name
        description="Handle Slack-related tasks like sending messages using tools provided.",
        instruction="You are the Slack Agent. Your ONLY task is interacts with Slack workspace using tools provided. Do not perform any other actions.",
        tools=tools1,
    )

    return slack_agent, exit_stack