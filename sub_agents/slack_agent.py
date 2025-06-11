from google.adk.agents import LlmAgent    
from google.adk.agents import Agent    
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import os
from dotenv import load_dotenv
import asyncio
load_dotenv('../.env')
SLACK_MCP_URL = os.getenv('SLACK_MCP_URL', "https://mcp.pipedream.net/e23c22c5-a414-47db-907f-cb0ca7690055/slack")
# MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT')

async def get_slack_agent():

    # print(f"SLACK_MCP_URL: {SLACK_MCP_URL}")

    # tools1, exit_stack = await MCPToolset.from_server(
    #         # connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")
    #         connection_params=SseServerParams(url=SLACK_MCP_URL)
    #         # connection_params=StdioServerParameters(
    #         #     command= "npx",
    #         #     args = [
    #         #         "-y",
    #         #         "supergateway",
    #         #         "--sse",
    #         #         "https://mcp.pipedream.net/e23c22c5-a414-47db-907f-cb0ca7690055/slack"
    #         #     ]
    #         # )
    # )
    # print(f"Fetched {len(tools1)} tools from Slack MCP server.")
    slack_agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="slack_agent", # Keep original name
        description="Handle Slack-related tasks like sending messages using tools provided.",
        instruction="You are the Slack Agent. Your ONLY task is interacts with Slack workspace using tools provided. Do not perform any other actions. When you receive a request to send a message to a user (use tool SLACK_SEND_MESSAGE_TO_USER_OR_GROUP to send DM), find the user's ID (use the `SLACK_LIST_USERS` tool to find the user ID) and then identify the user and the message before sending.",
        tools=[MCPToolset(
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
            )],
    )

    return slack_agent



async def async_main():
    slack_agent = await get_slack_agent()
    # slack_agent = LlmAgent(
    #     model="gemini-2.0-flash",
    #     name="slack_agent",
    #     description="Handle web automation tasks using Playwright tools provided.",
    #     instruction="You are the Playwright Agent. Your task is to interact with web browsers using the provided tools. Do not perform any other actions.",
    #     tools=[MCPToolset(
    #             connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")

    #     )],
    # )
    session_service = InMemorySessionService()
    session = await session_service.create_session(state={}, app_name='mcp_app111', user_id='user_app111')
    runner = Runner(app_name='mcp_app111', session_service=session_service, agent=slack_agent)
    

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
        # if exit_stack: # Đảm bảo exit_stack tồn tại trước khi gọi aclose
        #     await exit_stack.aclose()
        # if exit_stack: # Đảm bảo exit_stack tồn tại trước khi gọi aclose
        #     try:
        #         await exit_stack.aclose()
        #     except Exception as e:
        #         print(f"Error during exit_stack.aclose(): {e}")
        print("Cleanup complete.")

if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An unhandled error occurred in main: {e}")
        import traceback
        traceback.print_exc()