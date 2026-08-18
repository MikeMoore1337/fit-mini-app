"""Validate and import a reviewed local food catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the manifest and records without writing to the database",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "backend"))

    from fitminiapp_api.services.food_import import import_food_catalog, load_food_catalog

    catalog = load_food_catalog(args.catalog)
    if args.dry_run:
        print(f"Validated {len(catalog.foods)} food records from {catalog.source.name}")
        return

    from fitminiapp_api.db.session import get_session_context

    with get_session_context() as db:
        result = import_food_catalog(db, catalog)
    print(f"Imported food catalog: created={result.created}, updated={result.updated}")


if __name__ == "__main__":
    main()
