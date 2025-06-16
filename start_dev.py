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
    os.chdir(backend_dir)
    
    # Start backend with uvicorn
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    return subprocess.Popen(cmd, cwd=backend_dir)

def run_frontend():
    """Start the Vite frontend development server."""
    frontend_dir = Path(__file__).parent / "fronted"
    os.chdir(frontend_dir)
    
    # Start frontend with npm
    cmd = ["npm", "run", "dev"]
    return subprocess.Popen(cmd, cwd=frontend_dir)

def main():
    """Main function to start both servers."""
    print("🚀 Starting Extractra development servers...")
    
    # Start backend
    print("📡 Starting backend server...")
    backend_process = run_backend()
    time.sleep(2)  # Give backend time to start
    
    # Start frontend
    print("🎨 Starting frontend server...")
    frontend_process = run_frontend()
    
    print("\n✅ Development servers started!")
    print("📡 Backend: http://localhost:8000")
    print("🎨 Frontend: http://localhost:5173")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n⚠️  Press Ctrl+C to stop both servers")
    
    try:
        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for graceful shutdown
        backend_process.wait()
        frontend_process.wait()
        
        print("✅ Servers stopped successfully!")

if __name__ == "__main__":
    main() 