import json
import time
import schedule
import signal
import sys

# Global flag to control our main execution loop
running = True

def handle_shutdown(signum, frame):
    """Gracefully handles OS signals like SIGINT (Ctrl+C) or SIGTERM."""
    global running
    print("\nShutdown signal received. Cleaning up background scheduler...")
    running = False

def setup_scheduler(scheduled_time: str, bg_task, *args):
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Schedule the job dynamically based on config
    schedule.every().day.at(scheduled_time).do(bg_task, *args)
    print(f"Job scheduled daily at {scheduled_time}")

    # Keep the background process alive to listen for the scheduled time
    while running:
        schedule.run_pending()
        time.sleep(1) # Sleep to avoid heavy CPU usage
        
    print("Scheduler stopped safely. Exiting main process.")
