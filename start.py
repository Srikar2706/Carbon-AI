#!/usr/bin/env python3
"""
Startup script for the Agentic AI Carbon Ranker
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
        print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    return True

def run_demo():
    """Run the demo script"""
    print("\nRunning Carbon Ranker Demo...")
    try:
        subprocess.run([sys.executable, "demo.py"])
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error running demo: {e}")

def start_server():
    """Start the web server"""
    print("\nStarting web server...")
    print("Dashboard will be available at: http://localhost:8000")
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

def main():
    """Main startup function"""
    print("Carbon AI MVP")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("Please run this script from the Carbon-AI directory")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Run demo script (recommended for first time)")
    print("2. Start web server")
    print("3. Both (demo then server)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        run_demo()
    elif choice == "2":
        start_server()
    elif choice == "3":
        run_demo()
        input("\nPress Enter to start the web server...")
        start_server()
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
