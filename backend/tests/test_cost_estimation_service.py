from __future__ import annotations

from pathlib import Path

from backend.db import ensure_core_tables, get_connection
from backend.services.cost_estimation_service import PRICING_UNAVAILABLE, get_test_cost


def _setup_pricing(db_file: Path) -> None:
    with get_connection(db_file) as conn:
        ensure_core_tables(conn)
        conn.execute(
            """
            INSERT INTO country_test_pricing(country, city, test_name, price_usd, source_note)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("US", None, "HbA1c", 44.0, "test fixture"),
        )
        conn.execute(
            """
            INSERT INTO country_test_pricing(country, city, test_name, price_usd, source_note)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("US", "New York", "HbA1c", 50.0, "test fixture"),
        )
        conn.commit()


def test_known_country_and_city_returns_city_price(tmp_path: Path) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _setup_pricing(db_file)
    result = get_test_cost(
        test_name="HbA1c",
        country="US",
        city="New York",
        insurance_coverage=0.0,
        db_path=str(db_file),
    )
    assert result["gross_cost_usd"] == 50.0
    assert result["pricing_source"] == "country_city"
    assert result["pricing_uncertain"] is False


def test_unknown_country_uses_global_fallback_and_type8(tmp_path: Path) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _setup_pricing(db_file)
    result = get_test_cost(
        test_name="HbA1c",
        country="UnknownLand",
        insurance_coverage=0.0,
        db_path=str(db_file),
    )
    assert result["pricing_source"] == "global_fallback"
    assert result["pricing_uncertain"] is True
    assert result["uncertainty_type"] == PRICING_UNAVAILABLE


def test_insurance_coverage_reduces_net_cost(tmp_path: Path) -> None:
    db_file = tmp_path / "clinicaliq.db"
    _setup_pricing(db_file)
    result = get_test_cost(
        test_name="HbA1c",
        country="US",
        insurance_coverage=0.8,
        db_path=str(db_file),
    )
    assert result["gross_cost_usd"] == 44.0
    assert result["net_cost_usd"] == 8.8
