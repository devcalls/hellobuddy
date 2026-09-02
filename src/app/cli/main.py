import argparse
import os
import sys

from app.cli.job_search import run_job_search
from app.cli.resume import parse_resume

VERSION = "1.0.1"

def display_welcome_screen():
    """
    Display HelloBuddy welcome banner.
    """

    os.system(
        "cls" if os.name == "nt" else "clear"
    )

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

    print("-" * 60)

    print("-" * 50) # Visual separator line
    MAROON = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    print(CYAN + banner)
    print(f"Welcome to HelloBuddy [Version {VERSION}]" + RESET + "\n")


def build_parser():

    parser = argparse.ArgumentParser(
        prog="hellobuddy",
        description=(
            "HelloBuddy - Personal productivity "
            "and career assistant"
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # ==================================================
    # JOB SEARCH
    # ==================================================

    subparsers.add_parser(
        "job-search",
        help="Start the job search scheduler",
    )

    # ==================================================
    # RESUME
    # ==================================================

    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume and ATS operations",
    )

    resume_subparsers = (
        resume_parser.add_subparsers(
            dest="resume_command"
        )
    )

    # resume parse

    parse_parser = (
        resume_subparsers.add_parser(
            "parse",
            help=(
                "Parse a PDF/DOCX/TXT resume "
                "into ResumeAST"
            ),
        )
    )

    parse_parser.add_argument(
        "file_path",
        help=(
            "Path to PDF, DOCX or TXT resume"
        ),
    )

    parse_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help=(
            "Write ResumeAST to JSON file"
        ),
    )

    return parser, resume_parser


def main():

    parser, resume_parser = (
        build_parser()
    )

    args = parser.parse_args()

    # No command
    if args.command is None:

        display_welcome_screen()

        parser.print_help()

        return 0

    # Job search
    if args.command == "job-search":

        return run_job_search()

    # Resume
    if args.command == "resume":

        if args.resume_command is None:

            resume_parser.print_help()

            return 0

        if args.resume_command == "parse":

            return parse_resume(
                file_path=args.file_path,
                output=args.output,
            )

    parser.print_help()

    return 1


if __name__ == "__main__":
    sys.exit(main())