from app.cli.util import display_welcome_screen
import argparse
import sys

from app.cli.job_search import run_job_search
from app.cli.resume import (
    optimize_resume,
    parse_resume,
)

VERSION = "1.0.1"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="hellobuddy",
        description=("HelloBuddy - Personal productivity " "and career assistant"),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command")

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

    resume_subparsers = resume_parser.add_subparsers(dest="resume_command")

    # --------------------------------------------------
    # resume parse
    # --------------------------------------------------

    parse_parser = resume_subparsers.add_parser(
        "parse",
        help="Parse a resume into ResumeAST",
    )

    parse_parser.add_argument(
        "file_path",
        help="Path to PDF, DOCX or TXT resume",
    )

    parse_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write ResumeAST to JSON file",
    )

    # --------------------------------------------------
    # resume optimize
    # --------------------------------------------------

    optimize_parser = resume_subparsers.add_parser(
        "optimize",
        help="Analyze and optimize a resume for ATS",
    )

    optimize_parser.add_argument(
        "file_path",
        help="Path to PDF, DOCX, TXT resume or ResumeAST JSON",
    )

    optimize_parser.add_argument(
        "--input-type",
        choices=["resume", "ast"],
        default="resume",
        help=("Input type: resume document or ResumeAST JSON. " "Defaults to resume."),
    )

    optimize_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write optimization result to JSON file",
    )

    optimize_parser.add_argument(
        "--mode",
        choices=[
            "general_ats",
            "targeted_jd",
        ],
        default="general_ats",
        help=("Optimization mode. " "Defaults to general_ats."),
    )

    optimize_parser.add_argument(
        "--section",
        action="append",
        choices=[
            "summary",
            "experience",
            "skills",
            "projects",
            "education",
            "certifications",
        ],
        default=None,
        help=("Section to optimize. Can be specified " "multiple times."),
    )

    return parser, resume_parser


def main():
    parser, resume_parser = build_parser()

    args = parser.parse_args()

    # ==================================================
    # No command
    # ==================================================

    if args.command is None:
        display_welcome_screen(VERSION)
        parser.print_help()
        return 0

    # ==================================================
    # Job search
    # ==================================================

    if args.command == "job-search":
        return run_job_search()

    # ==================================================
    # Resume
    # ==================================================

    if args.command == "resume":

        if args.resume_command is None:
            resume_parser.print_help()
            return 0

        # --------------------------------------------------
        # resume parse
        # --------------------------------------------------

        if args.resume_command == "parse":
            return parse_resume(
                file_path=args.file_path,
                output=args.output,
            )

        # --------------------------------------------------
        # resume optimize
        # --------------------------------------------------

        if args.resume_command == "optimize":
            return optimize_resume(
                file_path=args.file_path,
                output=args.output,
                mode=args.mode,
                sections=args.section,
                input_type=args.input_type,
            )

    parser.print_help()

    return 1


if __name__ == "__main__":
    sys.exit(main())
