#!/usr/bin/env python
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 Starting Simple Contract Assistant...")
    print("=" * 50)
    
    # Start backend
    print("\n📡 Starting backend...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000"],
        cwd=Path(__file__).parent
    )
    
    time.sleep(2)
    
    # Start frontend
    print("🖥️  Starting frontend...")
    frontend = subprocess.Popen(
        [sys.executable, "frontend/app.py"],
        cwd=Path(__file__).parent
    )
    
    print("\n✅ Ready!")
    print("📊 Opening browser...")
    time.sleep(2)
    webbrowser.open("http://localhost:7860")
    
    print("\nPress Ctrl+C to stop")
    
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        backend.terminate()
        frontend.terminate()
        print("✅ Done")

if __name__ == "__main__":
    main()
