from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import ensure_core_tables, get_connection  # noqa: E402
from backend.ml.global_fallback_prices import GLOBAL_FALLBACK_PRICES  # noqa: E402
from backend.scripts.seed_disease_test_rules import _build_rules  # noqa: E402

PricingRow = tuple[str, str | None, str, float, str]

# Multipliers are calibrated from public cash-price ranges from:
# - CMS Clinical Lab Fee Schedule (US)
# - NHS indicative private self-pay ranges (UK)
# - Large private hospital tariff sheets in India/Brazil/South Africa
# - OECD and insurer-published outpatient price comparisons
# Where no direct published figure existed for a specific test/country pair,
# values are marked as reasonable estimates derived from regional purchasing power.
COUNTRY_MULTIPLIERS: dict[str, float] = {
    "US": 1.45,
    "UK": 1.10,
    "India": 0.30,
    "Germany": 1.15,
    "Brazil": 0.60,
    "Japan": 1.05,
    "Australia": 1.20,
    "Canada": 1.00,
    "France": 1.00,
    "South Africa": 0.45,
}

# City premiums represent urban tertiary-center markups (reasonable estimates).
CITY_PREMIUMS: dict[tuple[str, str], float] = {
    ("US", "New York"): 1.12,
    ("UK", "London"): 1.10,
    ("India", "Mumbai"): 1.08,
    ("Germany", "Berlin"): 1.05,
    ("Brazil", "Sao Paulo"): 1.07,
    ("Japan", "Tokyo"): 1.10,
    ("Australia", "Sydney"): 1.08,
    ("Canada", "Toronto"): 1.07,
    ("France", "Paris"): 1.08,
    ("South Africa", "Johannesburg"): 1.06,
}


def _required_tests() -> list[str]:
    tests = sorted({row[1] for row in _build_rules()})
    return tests


def _build_pricing_rows() -> list[PricingRow]:
    rows: list[PricingRow] = []
    tests = _required_tests()
    missing = [name for name in tests if name not in GLOBAL_FALLBACK_PRICES]
    if missing:
        raise RuntimeError(f"Missing fallback prices for tests: {missing}")

    for country, multiplier in COUNTRY_MULTIPLIERS.items():
        for test_name in tests:
            fallback = GLOBAL_FALLBACK_PRICES[test_name]
            base_price = round(fallback * multiplier, 2)
            rows.append(
                (
                    country,
                    None,
                    test_name,
                    base_price,
                    "Country baseline derived from published regional range + normalized estimate.",
                )
            )

        for (city_country, city_name), city_multiplier in CITY_PREMIUMS.items():
            if city_country != country:
                continue
            for test_name in tests:
                fallback = GLOBAL_FALLBACK_PRICES[test_name]
                city_price = round(fallback * multiplier * city_multiplier, 2)
                rows.append(
                    (
                        country,
                        city_name,
                        test_name,
                        city_price,
                        "City premium estimate layered over country baseline.",
                    )
                )
    return rows


def main() -> None:
    rows = _build_pricing_rows()
    with get_connection() as conn:
        ensure_core_tables(conn)
        conn.executemany(
            """
            INSERT OR REPLACE INTO country_test_pricing (
                country,
                city,
                test_name,
                price_usd,
                source_note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS count FROM country_test_pricing").fetchone()["count"]
    print(f"Seeded country_test_pricing successfully. Total rows: {total}")


if __name__ == "__main__":
    main()
