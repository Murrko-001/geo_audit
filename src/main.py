import argparse

from src.data_loader import load_posts_wrapper
from src.reporter import Reporter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GymBeam GEO audit",
        epilog=(
            "If neither the --csv nor the --html flag is specified, "
            "the application exports to both CSV and HTML by default."),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    p.add_argument(
        "--wp",
        action="store_true",
        help="Use WordPress API (use local JSON otherwise).",
    )

    p.add_argument(
        "--per-page",
        type=int,
        default=10,
        help="Number of articles to load (default: 10).",
    )

    p.add_argument(
        "--csv",
        action="store_true",
        help="Export the report to CSV.",
    )

    p.add_argument(
        "--html",
        action="store_true",
        help="Export the report to HTML.",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()
    reporter = Reporter()

    if not args.csv and not args.html:
        args.csv = True
        args.html = True

    posts = load_posts_wrapper(use_wp=args.wp, per_page=args.per_page)
    reporter.do_report(posts, report_to_html=args.html, report_to_csv=args.csv)


if __name__ == "__main__":
    main()
