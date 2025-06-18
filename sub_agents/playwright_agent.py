from google.adk.agents import LlmAgent    
from google.adk.agents import Agent   
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
from dotenv import load_dotenv
from google.genai import types
import os
import asyncio
import copy

load_dotenv('../.env')

MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT', 8931)


MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT', 8931)
print(f"MCP_SERVER_PORT, tải env ok: {MCP_SERVER_PORT}")
async def get_playwright_agent():
    # playwright_tools, exit_stack = await MCPToolset(
    #         connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")
    #         # connection_params=StdioServerParameters(
    #         #     command='npx', 
    #         #     args=["-y",    # Arguments for the command
    #         #         "@playwright/mcp@latest",
    #         #         "--port",
    #         #         "8931",
    #         #     ],
    #         # ) 
    # )
    # print(f"Fetched {len(playwright_tools)} tools from Playwright MCP server.")
    playwright_agent = LlmAgent(
        model="gemini-2.0-flash",
        name="playwright_agent",
        description="Handle web automation tasks using Playwright tools provided.",
        instruction="You are the Playwright Agent. Your task is to interact with web browsers using the provided tools. If you don't know the answer, let move on to the root agent to handle the task.",
        tools=[MCPToolset(
            connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")
            # connection_params=StdioServerParameters(
            #     command='npx', 
            #     args=["-y",    # Arguments for the command
            #         "@playwright/mcp@latest",
            #         # "--port",
            #         # "8931",
            #     ],
            # )
        )],
    )

    return playwright_agent


async def async_main():
    playwright_agent = await get_playwright_agent()
    # playwright_agent = LlmAgent(
    #     model="gemini-2.0-flash",
    #     name="playwright_agent",
    #     description="Handle web automation tasks using Playwright tools provided.",
    #     instruction="You are the Playwright Agent. Your task is to interact with web browsers using the provided tools. Do not perform any other actions.",
    #     tools=[MCPToolset(
    #             connection_params=SseServerParams(url=f"http://localhost:{MCP_SERVER_PORT}/sse")

    #     )],
    # )
    session_service = InMemorySessionService()
    session = await session_service.create_session(state={}, app_name='mcp_app111', user_id='user_app111')
    runner = Runner(app_name='mcp_app111', session_service=session_service, agent=playwright_agent)
    

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