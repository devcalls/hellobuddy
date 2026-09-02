import sys
import signal

from app.services.job_search.scheduler import setup_scheduler
from app.services.job_search.job_orchestrator_service import (
    orchestrate,
)
from app.config.job_settings import JobSearchSettings

running = True


def handle_shutdown(signum, frame):
    """
    Gracefully handle Ctrl+C / SIGTERM.
    """

    global running

    print()
    print("Shutdown signal received. " "Cleaning up background scheduler...")

    running = False


def run_job_search() -> int:

    signal.signal(
        signal.SIGINT,
        handle_shutdown,
    )

    signal.signal(
        signal.SIGTERM,
        handle_shutdown,
    )

    try:

        settings = JobSearchSettings()

        scheduled_time = settings.scheduler.schedule_time

        setup_scheduler(
            scheduled_time,
            orchestrate,
            settings,
        )

        print()
        print("Background scheduler is now running.")

        print("Press Ctrl+C to exit.")

        # Keep the process alive.
        signal.pause()

        return 0

    except KeyboardInterrupt:

        print()
        print("👋 Shutdown signal received. " "Exiting hellobuddy...")

        return 0

    except Exception as error:

        print()
        print("=" * 60)
        print("🚨 AN UNEXPECTED APPLICATION " "ERROR OCCURRED")
        print("=" * 60)

        print(f"Details: {error}")

        print("=" * 60)
        print()

        return 1
