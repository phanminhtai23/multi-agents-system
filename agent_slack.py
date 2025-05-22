import asyncio
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
import os

from composio_openai import ComposioToolSet, App
# from openai import OpenAI


# Load environment variables
load_dotenv('./.env')
SLACK_MCP_URL = os.getenv('SLACK_MCP_URL')

# --- Step 1: Agent Definition (Không thay đổi) ---
async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    print("Connecting to MCP server to fetch tools...")
    try:
        tools, exit_stack = await MCPToolset.from_server(
            # connection_params=SseServerParams(url="http://localhost:8931/sse")
            connection_params=SseServerParams(url=SLACK_MCP_URL)
            # connection_params=StdioServerParameters(
            #     command='npx',
            #     args=["-y",    # Arguments for the command
            #         "@modelcontextprotocol/server-slack",
            #         # "--vision",
            #     ],
            #     env = {
            #         "SLACK_BOT_TOKEN": "",
            #         "SLACK_TEAM_ID": "",
            #         "SLACK_CHANNEL_IDS": ""
            #     }
            #     # env = {
            #     #     "SLACK_BOT_TOKEN": "",
            #     #     "SLACK_TEAM_ID": "",
            #     #     "SLACK_CHANNEL_IDS": ""
            #     # }
            # ) 
        )

        print(f"Fetched {len(tools)} tools from MCP server.")
        # print(f"Fetched {len(tools)} tools from MCP server.")
        root_agent = LlmAgent(
            model='gemini-2.0-flash', # Hoặc model bạn muốn dùng
            name='slack_interactive_assistant',
            instruction='This server enables LLMs to interact with Slack workspaces, including sending messages, reading channels, and responding to users. I will help you manage your Slack communications effectively and professionally.',
            tools=tools,
        )
        return root_agent, exit_stack
    except Exception as e:
        print(f"Error connecting to MCP server or creating agent: {e}")
        return None, None

# --- Step 2: Main Execution Logic with Interactive Loop ---
async def async_main():
    session_service = InMemorySessionService()
    artifacts_service = InMemoryArtifactService() # Thường là tùy chọn nếu không dùng artifacts

    # Tạo agent và exit_stack một lần ở đầu
    root_agent, exit_stack = await get_agent_async()
    if not root_agent or not exit_stack:
        print("Failed to initialize agent. Exiting.")
        return

    # Tạo session một lần cho toàn bộ vòng lặp tương tác
    # Điều này cho phép agent có thể nhớ ngữ cảnh giữa các lượt (tùy thuộc vào cách LlmAgent và session_service xử lý)
    session = session_service.create_session(
        state={}, app_name='slack_interactive_assistant', user_id='slack_interactive_assistant'
    )
    print(f"Session created with ID: {session.id}")

    runner = Runner(
        app_name='slack_interactive_assistant',
        agent=root_agent,
        artifact_service=artifacts_service,
        session_service=session_service,
    )

    print("\nAgent is ready. Type 'quit' or 'exit' to stop.")
    print("-------------------------------------------------")

    try:
        while True:
            try:
                # Sử dụng input() thông thường, nhưng chạy nó trong executor để không block event loop
                query = await asyncio.to_thread(input, ">>> You: ")
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    # Xử lý nếu đang ở trong môi trường như Jupyter notebook
                    # nơi input() có thể gây vấn đề với event loop đang chạy
                    print("Please type your query in the next prompt (workaround for input issue).")
                    await asyncio.sleep(0.1) # Cho phép event loop xử lý
                    query = input(">>> You (sync): ") # Thử input đồng bộ
                else:
                    raise e


            if query.lower() in ['quit', 'exit']:
                print("Exiting chat...")
                break

            if not query.strip(): # Bỏ qua nếu người dùng chỉ nhấn Enter
                continue

            user_message_content = types.Content(role='user', parts=[types.Part(text=query)])

            print("<<< Agent thinking...")
            final_response_text = "Agent did not produce a final response." # Giá trị mặc định
            has_responded = False

            async for event in runner.run_async(
                session_id=session.id, user_id=session.user_id, new_message=user_message_content
            ):
                # Bỏ comment để debug:
                # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response_text = event.content.parts[0].text
                    elif event.actions and event.actions.escalate:
                        final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    else:
                        # Đôi khi final_response có thể không có content.parts trực tiếp
                        # mà có thể là một thông báo ngầm hoặc chỉ là kết thúc tool call.
                        # Tùy thuộc vào cách agent được thiết kế.
                        # Trong trường hợp này, nếu không có text cụ thể, có thể giữ thông báo mặc định
                        # hoặc kiểm tra các thuộc tính khác của event.
                        pass # Giữ final_response_text mặc định hoặc xử lý khác
                    has_responded = True
                    break # Dừng khi có phản hồi cuối cùng

            if not has_responded and final_response_text == "Agent did not produce a final response.":
                 # Nếu agent không có final_response rõ ràng mà có thể chỉ thực thi tool
                 # bạn có thể muốn một thông báo khác.
                 # Hoặc kiểm tra event.intermediate_steps, event.actions nếu cần.
                 # Ví dụ, nếu có tool_code_output mà không có final LLM response:
                 # last_tool_output = ""
                 # async for ev_debug in runner.run_async(...): # phải chạy lại hoặc lưu trữ event
                 #    if ev_debug.tool_code_output: last_tool_output = ev_debug.tool_code_output.outputs[0].text
                 # if last_tool_output: final_response_text = f"[Tool executed, no explicit LLM response. Last output: {last_tool_output[:100]}...]"
                 pass # Giữ nguyên

            print(f"<<< Agent: {final_response_text}\n")

    except KeyboardInterrupt:
        print("\nCaught interrupt, exiting chat...")
    finally:
        # Dọn dẹp quan trọng
        print("Closing MCP server connection...")
        if exit_stack: # Đảm bảo exit_stack tồn tại trước khi gọi aclose
            await exit_stack.aclose()
        print("Cleanup complete.")

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An unhandled error occurred in main: {e}")
        import traceback
        traceback.print_exc()