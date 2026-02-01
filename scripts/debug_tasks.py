import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Ensure project root is on path when running script directly (e.g. debugger)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from stream2mediaserver.main_logic import MainLogic  # noqa: E402
from stream2mediaserver.parser import animeon_parser  # noqa: E402
from stream2mediaserver.utils.test_data_logger import TestDataLogger  # noqa: E402


def run_search(query: str) -> None:
    logic = MainLogic()
    results = asyncio.run(logic.search(query))
    print(f"Found {len(results)} results for '{query}'.")


def _search_one_provider(
    logic: MainLogic,
    provider_name: str,
    query: str,
) -> Tuple[str, List[Any]]:
    """Run search for a single provider (used from thread). Returns (provider_label, results)."""
    provider_class = logic.get_provider_class(provider_name)
    if not provider_class:
        return (provider_name, [])
    provider = provider_class(logic.config)
    provider_label = getattr(provider, "provider", provider_name)
    with TestDataLogger.context(provider_label, "searchAnime", "searchtitle"):
        results = provider.search_title(query)
    return (provider_label, results or [])


def _details_one_provider(
    logic: MainLogic,
    provider_name: str,
    url: str,
) -> Tuple[str, str, List[Any]]:
    """Load details for first result of a provider (used from thread). Returns (provider_label, url, series_list)."""
    provider_class = logic.get_provider_class(provider_name)
    if not provider_class:
        return (provider_name, url, [])
    provider = provider_class(logic.config)
    provider_label = getattr(provider, "provider", provider_name)
    with TestDataLogger.context(provider_label, "searchAnime", "detailspage"):
        raw = provider.load_details_page(url)
    if raw is None:
        return (provider_label, url, [])
    groups = raw if isinstance(raw, list) else [raw]
    return (provider_label, url, groups)


def _print_search_results(provider_label: str, results: List[Any]) -> None:
    """Print search results block for one provider."""
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


def _print_series_details(provider_label: str, url: str, groups: List[Any]) -> None:
    """Print details/series block for one provider. groups = List[SeriesGroup] from load_details_page."""
    total = sum(len(getattr(g, "episodes", [])) for g in groups)
    print(f"  Details: {url}")
    print(f"  Series: {total} item(s)")
    for group in groups:
        studio_name = getattr(group, "studio_name", "") or ""
        studio_id = getattr(group, "studio_id", "") or ""
        episodes = getattr(group, "episodes", []) or []
        label = studio_name or studio_id or "Unknown"
        print(f"  [{label}] ({len(episodes)} series)")
        for i, ep in enumerate(episodes, 1):
            series = getattr(ep, "series", "") or ""
            urls = getattr(ep, "urls", None)
            if not urls:
                urls = [getattr(ep, "url", "") or ""]
            print(f"    {i}. {series!s}")
            for u in urls:
                if u:
                    print(f"       {u}")


async def run_populate_test_data_async(query: str, dump_dir: Path) -> None:
    logic = MainLogic()
    TestDataLogger.configure(base_dir=dump_dir, enabled=True)
    provider_names = logic.enabled_provider_names()
    if not provider_names:
        print("No providers enabled.")
        return

    print(f"Query: {query!r}")
    print(f"Dump dir: {dump_dir}")
    print("-" * 60)

    # Run all provider searches in parallel
    search_tasks = [
        asyncio.to_thread(_search_one_provider, logic, name, query)
        for name in provider_names
    ]
    search_outcomes = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Build (provider_label -> results) and (provider_name -> urls) for details
    search_by_label: dict = {}
    details_tasks: List[Tuple[str, str, str]] = []  # (provider_name, provider_label, url)
    for name, outcome in zip(provider_names, search_outcomes):
        if isinstance(outcome, Exception):
            print(f"\n[{name}] Error: {outcome}")
            continue
        label, results = outcome
        search_by_label[label] = results
        urls_to_fetch: List[str] = []
        if results:
            # UAFlix: fetch 2 details – one with /serials/, one without (if both present)
            if name == "uaflix_provider":
                with_serials = next(
                    (r for r in results if "/serials/" in (getattr(r, "url", "") or getattr(r, "link", "") or "")),
                    None,
                )
                without_serials = next(
                    (r for r in results if "/serials/" not in (getattr(r, "url", "") or getattr(r, "link", "") or "")),
                    None,
                )
                if with_serials:
                    url = getattr(with_serials, "url", None) or getattr(with_serials, "link", None)
                    if url:
                        urls_to_fetch.append(url)
                if without_serials:
                    url = getattr(without_serials, "url", None) or getattr(without_serials, "link", None)
                    if url and url not in urls_to_fetch:
                        urls_to_fetch.append(url)
            else:
                first = results[0]
                first_url = getattr(first, "url", None) or getattr(first, "link", None)
                if first_url:
                    urls_to_fetch.append(first_url)
        for url in urls_to_fetch:
            details_tasks.append((name, label, url))

    # Run all details fetches in parallel
    details_outcomes = await asyncio.gather(
        *[
            asyncio.to_thread(_details_one_provider, logic, name, url)
            for name, _label, url in details_tasks
        ],
        return_exceptions=True,
    )

    # Map provider_label -> List[(url, series_list)]
    details_by_label: dict = {}
    for (name, label, url), outcome in zip(details_tasks, details_outcomes):
        if label not in details_by_label:
            details_by_label[label] = []
        if isinstance(outcome, Exception):
            details_by_label[label].append((url, []))
            continue
        _lab, _url, series_list = outcome
        details_by_label[label].append((_url, series_list))

    # Print in stable order (by provider_names -> label)
    seen_labels = set()
    for name in provider_names:
        provider_class = logic.get_provider_class(name)
        if not provider_class:
            continue
        provider = provider_class(logic.config)
        label = getattr(provider, "provider", name)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        results = search_by_label.get(label, [])
        _print_search_results(label, results)
        if label in details_by_label:
            for url, series_list in details_by_label[label]:
                _print_series_details(label, url, series_list)
    print()


def run_populate_test_data(query: str, dump_dir: Path) -> None:
    asyncio.run(run_populate_test_data_async(query, dump_dir))


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
