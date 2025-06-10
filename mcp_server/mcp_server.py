import subprocess
import os
import signal
import atexit
import time
# from dotenv import load_dotenv

# load_dotenv('../.env')

# MCP_SERVER_PORT = os.getenv('MCP_SERVER_PORT')
# print(f"MCP_SERVER_PORT: {MCP_SERVER_PORT}")
# Global variable để lưu MCP process
mcp_process = None

def start_mcp_server(port=8931):
    """
    Khởi động MCP server với Playwright
    Args:
        port (int): Port để chạy MCP server, mặc định 8931
    Returns:
        subprocess.Popen: Process object của MCP server
    """
    global mcp_process
    
    print(f"Starting Playwright MCP server on port {port}...")
    
    try:
        mcp_process = subprocess.Popen(
            ["npx", "-y", "@playwright/mcp@latest", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True  # Cần thiết cho Windows
        )
        
        # Đợi server khởi động
        time.sleep(3)
        
        # Kiểm tra xem process có chạy không
        if mcp_process.poll() is None:
            print(f"✅ MCP server started successfully on port {port}")
            return mcp_process
        else:
            print(f"❌ Failed to start MCP server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        return None

def stop_mcp_server():
    """
    Dừng MCP server
    Returns:
        bool: True nếu dừng thành công, False nếu có lỗi
    """
    global mcp_process
    
    if mcp_process and mcp_process.poll() is None:
        print("Stopping MCP server...")
        try:
            if os.name == 'nt':  # Windows
                mcp_process.terminate()
            else:  # Unix/Linux/Mac
                os.kill(mcp_process.pid, signal.SIGTERM)
                
            mcp_process.wait(timeout=5)
            print("✅ MCP server stopped successfully")
            return True
            
        except subprocess.TimeoutExpired:
            print("🔥 Force killing MCP server...")
            mcp_process.kill()
            return True
        except Exception as e:
            print(f"❌ Error stopping MCP server: {e}")
            return False
    else:
        print("MCP server is not running")
        return True

def get_mcp_process():
    """
    Trả về MCP process hiện tại
    Returns:
        subprocess.Popen: Process object hoặc None
    """
    return mcp_process

# Đảm bảo server sẽ tắt khi script kết thúc
def cleanup_mcp_server():
    stop_mcp_server()

atexit.register(cleanup_mcp_server)

# Nếu file được chạy trực tiếp
if __name__ == "__main__":
    server = start_mcp_server()
    if server:
        try:
            # Chờ cho đến khi có signal interrupt
            server.wait()
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            stop_mcp_server()