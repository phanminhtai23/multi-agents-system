from google.adk.agents import LlmAgent    
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters


async def get_slack_agent():

    playwright_tools, exit_stack = await MCPToolset.from_server(
            # connection_params=SseServerParams(url="http://localhost:8931/sse")
            connection_params=SseServerParams(url="http://localhost:8931/sse")
            # connection_params=StdioServerParameters(
            #     command='python',
            #     args=["-y",    # Arguments for the command
            #         "@playwright/mcp@latest",
            #         # "--vision",
            #     ],
            # ) 
    )
    print(f"Fetched {len(playwright_tools)} tools from Slack MCP server.")
    slack_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="slack_agent", # Keep original name
        description="Handle Slack-related tasks like sending messages using tools provided.",
        instruction="You are the Slack Agent. Your ONLY task is interacts with Slack workspace using tools provided. Do not perform any other actions.",
        tools=playwright_tools,
    )

    return slack_agent