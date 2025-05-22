import subprocess
import os
import signal
import atexit

# Khởi động MCP server với Playwright
print("Starting Playwright MCP server...")
mcp_process = subprocess.Popen(
    ["npx", "-y", "@playwright/mcp@latest", "--port", "8931"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True  # Cần thiết cho Windows
)

# Đảm bảo server sẽ tắt khi script kết thúc
def cleanup_mcp_server():
    if mcp_process:
        print("Shutting down MCP server...")
        if os.name == 'nt':  # Windows
            os.kill(mcp_process.pid, signal.CTRL_C_EVENT)
        else:  # Unix/Linux/Mac
            os.kill(mcp_process.pid, signal.SIGTERM)
        mcp_process.wait()

atexit.register(cleanup_mcp_server)

# Đợi server khởi động (có thể điều chỉnh thời gian)
import time
time.sleep(3)  # Đợi 3 giây