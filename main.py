from parent_agent.parent_agent import async_main
from mcp_server.mcp_server import start_mcp_server, stop_mcp_server
import asyncio
from dotenv import load_dotenv
import os

import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
os.environ["GOOGLE_API_KEY"] = ""

load_dotenv("./.env")
print(f"DEBUG: GOOGLE_API_KEY sau khi load_dotenv: {os.getenv('GOOGLE_API_KEY')}")

MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT', 8931)
# print("MCP_SERVER_PORT", MCP_SERVER_PORT)

if __name__ == '__main__':
    try:
        # Khởi động MCP server trước
        # print("🚀 Đang khởi động MCP server...")
        mcp_process = start_mcp_server(MCP_SERVER_PORT)

        # Chạy main agent
        print("🤖 Đang khởi động Parent Agent...")
        asyncio.run(async_main())
        
    except KeyboardInterrupt:
        print("\n🛑 Nhận được tín hiệu dừng...")
    except Exception as e:
        print(f"❌ Lỗi không xử lý được trong main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Đảm bảo dừng MCP server khi kết thúc
        print("🔧 Đang dọn dẹp và dừng MCP server...")
        stop_mcp_server()
        print("👋 Tạm biệt!")