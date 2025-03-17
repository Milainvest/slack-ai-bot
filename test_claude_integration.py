#!/usr/bin/env python3
"""
Test script to verify Claude Desktop integration with CodeMCP.
This script simply prints information about the project and environment.
"""

import os
import sys
import platform
from datetime import datetime

def main():
    print("=== Claude Desktop Integration Test ===")
    print(f"Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Current Directory: {os.getcwd()}")
    
    print("\n=== Project Files ===")
    for file in sorted(os.listdir('.')):
        if os.path.isfile(file):
            size = os.path.getsize(file)
            print(f"- {file} ({size} bytes)")
    
    print("\n=== Environment Variables ===")
    # Only print non-sensitive environment variables or placeholders for sensitive ones
    env_vars = {
        "SLACK_BOT_TOKEN": "Present" if "SLACK_BOT_TOKEN" in os.environ else "Not set",
        "SLACK_SIGNING_SECRET": "Present" if "SLACK_SIGNING_SECRET" in os.environ else "Not set",
        "OPENAI_API_KEY": "Present" if "OPENAI_API_KEY" in os.environ else "Not set",
        "PORT": os.environ.get("PORT", "52987 (default)"),
        "HOST": os.environ.get("HOST", "0.0.0.0 (default)")
    }
    
    for key, value in env_vars.items():
        print(f"- {key}: {value}")
    
    print("\n=== Integration Test Complete ===")
    print("If you can see this output, Claude Desktop can successfully run Python scripts in your project!")

if __name__ == "__main__":
    main() 