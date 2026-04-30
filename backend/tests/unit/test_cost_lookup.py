from __future__ import annotations

from pathlib import Path

from backend.db import ensure_core_tables, get_connection
from backend.ml.uncertainty_engine import PRICING_UNAVAILABLE
from backend.services.cost_estimation_service import get_test_cost


def test_cost_lookup_prefers_city_then_country(isolated_db_path: Path) -> None:
    with get_connection(isolated_db_path) as conn:
        ensure_core_tables(conn)
        conn.executemany(
            "INSERT INTO country_test_pricing(country, city, test_name, price_usd, source_note) VALUES (?, ?, ?, ?, ?)",
            [
                ("US", None, "HbA1c", 44.0, "fixture"),
                ("US", "New York", "HbA1c", 50.0, "fixture"),
            ],
        )
        conn.commit()

    city = get_test_cost(test_name="HbA1c", country="US", city="New York", db_path=str(isolated_db_path))
    country = get_test_cost(test_name="HbA1c", country="US", insurance_coverage=0.5, db_path=str(isolated_db_path))

    assert city["gross_cost_usd"] == 50.0
    assert city["pricing_source"] == "country_city"
    assert country["net_cost_usd"] == 22.0
    assert country["pricing_source"] == "country_only"


def test_cost_lookup_unknown_country_returns_pricing_uncertainty(isolated_db_path: Path) -> None:
    result = get_test_cost(test_name="HbA1c", country="Atlantis", db_path=str(isolated_db_path))

    assert result["pricing_source"] == "global_fallback"
    assert result["pricing_uncertain"] is True
    assert result["uncertainty_type"] == PRICING_UNAVAILABLE
