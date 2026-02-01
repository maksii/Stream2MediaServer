import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on path when running script directly (e.g. debugger)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from stream2mediaserver.main_logic import MainLogic
from stream2mediaserver.parser import animeon_parser
from stream2mediaserver.utils.test_data_logger import TestDataLogger


def run_search(query: str) -> None:
    logic = MainLogic()
    results = asyncio.run(logic.search(query))
    print(f"Found {len(results)} results for '{query}'.")


def run_populate_test_data(query: str, dump_dir: Path) -> None:
    logic = MainLogic()
    TestDataLogger.configure(base_dir=dump_dir, enabled=True)
    print(f"Query: {query!r}")
    print(f"Dump dir: {dump_dir}")
    print("-" * 60)
    for provider_name in logic.enabled_provider_names():
        provider_class = logic.get_provider_class(provider_name)
        if not provider_class:
            continue
        provider = provider_class(logic.config)
        provider_label = getattr(provider, "provider", provider_name)
        with TestDataLogger.context(provider_label, "searchAnime", "searchtitle"):
            results = provider.search_title(query)
        # Always print provider and results (even if empty)
        print(f"\n[{provider_label}]")
        print(f"  Found: {len(results)} result(s)")
        for i, r in enumerate(results, 1):
            title = getattr(r, "title", "") or ""
            title_eng = getattr(r, "title_eng", "") or ""
            link = getattr(r, "link", "") or getattr(r, "url", "") or ""
            line = f"  {i}. {title!s}"
            if title_eng and str(title_eng) != "Not Specified":
                line += f" / {title_eng!s}"
            print(line)
            if link:
                print(f"     {link}")
        if not results:
            continue
        first = results[0]
        url = getattr(first, "url", None) or getattr(first, "link", None)
        if not url:
            continue
        with TestDataLogger.context(provider_label, "searchAnime", "detailspage"):
            provider.load_details_page(url)
    print()


def run_initiate_scrap(database: str) -> None:
    conn = animeon_parser.create_connection(database)
    if conn is None:
        raise RuntimeError("Failed to connect to database.")
    animeon_parser.setup_database(conn)
    animeon_parser.initiate_scrap(conn)


def run_delta(database: str) -> None:
    conn = animeon_parser.create_connection(database)
    if conn is None:
        raise RuntimeError("Failed to connect to database.")
    animeon_parser.setup_database(conn)
    animeon_parser.delta(conn)


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug helpers for Stream2MediaServer")
    parser.add_argument(
        "action", choices=["search", "initiate_scrap", "delta", "populate_test_data"]
    )
    parser.add_argument(
        "--query", default="Example Anime", help="Search query for main_logic search"
    )
    parser.add_argument(
        "--db", default="data/animeon.sqlite", help="SQLite database path"
    )
    parser.add_argument(
        "--dump-dir",
        default="data/test_data",
        help="Directory for captured provider responses",
    )
    args = parser.parse_args()

    if args.action == "search":
        run_search(args.query)
        return

    if args.action == "initiate_scrap":
        run_initiate_scrap(args.db)
        return

    if args.action == "populate_test_data":
        run_populate_test_data(args.query, Path(args.dump_dir))
        return

    run_delta(args.db)


if __name__ == "__main__":
    main()
