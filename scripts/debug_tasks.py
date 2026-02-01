import argparse
import asyncio

from stream2mediaserver.main_logic import MainLogic
from stream2mediaserver.parser import animeon_parser


def run_search(query: str) -> None:
    logic = MainLogic()
    results = asyncio.run(logic.search(query))
    print(f"Found {len(results)} results for '{query}'.")


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
    parser.add_argument("action", choices=["search", "initiate_scrap", "delta"])
    parser.add_argument(
        "--query", default="Naruto", help="Search query for main_logic search"
    )
    parser.add_argument(
        "--db", default="data/animeon.sqlite", help="SQLite database path"
    )
    args = parser.parse_args()

    if args.action == "search":
        run_search(args.query)
        return

    if args.action == "initiate_scrap":
        run_initiate_scrap(args.db)
        return

    run_delta(args.db)


if __name__ == "__main__":
    main()
