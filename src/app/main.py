import json
import sys
import time
import signal
import asyncio
import os

from app.services.job_search.scheduler import setup_scheduler
from app.services.job_search.job_orchestrator_service import (
    extract_jobs_send_email,
    orchestrate,
)

# from config.config import ConfigManager
from app.config.job_settings import JobSearchSettings
import os


def display_welcome_screen():
    # Clear the console screen for a clean startup
    # 'nt' is for Windows, 'posix' is for Mac/Linux
    os.system("cls" if os.name == "nt" else "clear")

    # The ASCII Art Banner
    banner = r"""
  _    _ ______ _      _      ____  
 | |  | |  ____| |    | |    / __ \ 
 | |__| | |__  | |    | |   | |  | |
 |  __  |  __| | |    | |   | |  | |
 | |  | | |____| |____| |___| |__| |
 |_|  |_|______|______|______\____/ 
                                    
  ____  _    _ _____  _____ __     __
 |  _ \| |  | |  __ \|  __ \\ \   / /
 | |_) | |  | | |  | | |  | |\ \_/ / 
 |  _ <| |  | | |  | | |  | | \   /  
 | |_) | |__| | |__| | |__| |  | |   
 |____/ \____/|_____/|_____/   |_|   
    """

    print("-" * 50)  # Visual separator line
    MAROON = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    print(CYAN + banner)
    print("Welcome to HelloBuddy Lite [Version 1.0.1]" + RESET + "\n")


def handle_shutdown(signum, frame):
    """Gracefully handles OS signals like SIGINT (Ctrl+C) or SIGTERM."""
    global running
    print("\nShutdown signal received. Cleaning up background scheduler...")
    running = False


def main():
    # 1. Register shutdown signals
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        # Load the scheduled time from config
        # config_manager = ConfigManager()
        settings = JobSearchSettings()
        # scheduled_time = config_manager.get_value("SCHEDULER", "JOB_TIME")
        scheduled_time = settings.scheduler.schedule_time

        # Start the scheduler with the extracted job function
        # async_wrapper = lambda: asyncio.run(orchestrate(settings))
        # setup_scheduler(scheduled_time, async_wrapper)

        # orchestrate(settings)
        setup_scheduler(scheduled_time, orchestrate, settings)

        print("Background scheduler is now running. Press Ctrl+C to exit.")

    except KeyboardInterrupt:
        # Catching Ctrl+C separately so it doesn't look like an error
        print("\n👋 Shutdown signal received. Exiting hellobuddy...")
        sys.exit(0)

    except Exception as error:
        # This catches ANY other subclass of Exception (ValueError, TypeError, NameError, etc.)
        print("\n" + "!" * 60)
        print("🚨 AN UNEXPECTED APPLICATION ERROR OCCURRED")
        print(f"Details: {error}")
        print("!" * 60 + "\n")

        # OPTIONAL: If you want to see exactly what line caused the crash
        # without blowing up the screen, uncomment the next line:
        # traceback.print_exc(limit=2)

        # Exit with error code 1 so the terminal runner knows it failed
        sys.exit(1)


if __name__ == "__main__":
    display_welcome_screen()
    main()
