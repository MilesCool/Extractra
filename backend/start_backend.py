#!/usr/bin/env python3
"""
Development server startup script.
Starts both frontend and backend servers concurrently.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_backend():
    """Start the FastAPI backend server."""
    backend_dir = Path(__file__).parent / "backend"
    project_root = Path(__file__).parent
    
    # 检查项目根目录的虚拟环境
    venv_paths = [
        project_root / ".venv",  # 标准虚拟环境目录
        project_root / "venv",   # 备选虚拟环境目录
        project_root / "env"     # 另一个备选目录
    ]
    
    python_executable = None
    venv_found = False
    
    # 查找虚拟环境中的 Python 可执行文件
    for venv_path in venv_paths:
        if venv_path.exists():
            if sys.platform.startswith('win'):
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                python_executable = str(python_exe)
                venv_found = True
                print(f"🐍 Found virtual environment: {venv_path}")
                break
    
    if not venv_found:
        print("⚠️  No virtual environment found in project root")
        print("💡 Please create a virtual environment first:")
        print("   python -m venv .venv")
        print("   .venv\\Scripts\\activate  # Windows")
        print("   source .venv/bin/activate  # Linux/Mac")
        print("   pip install -r backend/requirements.txt")
        return None
    
    # 检查是否安装了必要的依赖
    try:
        result = subprocess.run([python_executable, "-c", "import uvicorn"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ uvicorn not found in virtual environment")
            print("💡 Please install dependencies:")
            print(f"   {python_executable} -m pip install -r backend/requirements.txt")
            return None
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return None
    
    # 使用虚拟环境的 Python 启动后端
    cmd = [python_executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    print(f"🔧 Using virtual environment Python: {python_executable}")
    
    return subprocess.Popen(cmd, cwd=backend_dir)

def main():
    print("🚀 Starting Extractra backend server...")

    backend_process = run_backend()
    
    if backend_process is None:
        print("❌ Failed to start backend server")
        print("🛑 Exiting...")
        return
    
    print("\n✅ Backend server started!")
    print("📡 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    
    try:
        # Wait for both processes
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_process.terminate()
        
        # Wait for graceful shutdown
        backend_process.wait()
        
        print("✅ Servers stopped successfully!")

if __name__ == "__main__":
    main() 