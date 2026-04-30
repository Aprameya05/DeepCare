from __future__ import annotations

from dataclasses import dataclass

from backend.db import ensure_core_tables, get_connection
from backend.ml.global_fallback_prices import GLOBAL_FALLBACK_PRICES

PRICING_UNAVAILABLE = "PRICING_UNAVAILABLE"


@dataclass(frozen=True)
class CostLookupResult:
    test_name: str
    country: str
    city: str | None
    gross_cost_usd: float
    insurance_coverage_pct: float
    net_cost_usd: float
    pricing_source: str
    pricing_uncertain: bool
    uncertainty_type: str | None


def _normalize_coverage(insurance_coverage: float) -> float:
    value = float(insurance_coverage)
    if value > 1:
        value = value / 100.0
    return min(max(value, 0.0), 1.0)


def get_test_cost(
    *,
    test_name: str,
    country: str,
    city: str | None = None,
    insurance_coverage: float = 0.0,
    db_path: str | None = None,
) -> dict[str, object]:
    with get_connection(db_path) as conn:
        ensure_core_tables(conn)
        normalized_country = country.strip()
        normalized_city = city.strip() if city else None

        row = None
        if normalized_city:
            row = conn.execute(
                """
                SELECT price_usd
                FROM country_test_pricing
                WHERE LOWER(country) = LOWER(?)
                  AND LOWER(COALESCE(city, '')) = LOWER(?)
                  AND LOWER(test_name) = LOWER(?)
                LIMIT 1
                """,
                (normalized_country, normalized_city, test_name),
            ).fetchone()

        pricing_source = "country_city"
        pricing_uncertain = False
        uncertainty_type: str | None = None
        gross_cost = None

        # Fallback 1: country-only price.
        if row is None:
            pricing_source = "country_only"
            pricing_uncertain = True
            row = conn.execute(
                """
                SELECT price_usd
                FROM country_test_pricing
                WHERE LOWER(country) = LOWER(?)
                  AND city IS NULL
                  AND LOWER(test_name) = LOWER(?)
                LIMIT 1
                """,
                (normalized_country, test_name),
            ).fetchone()

        if row is not None:
            gross_cost = float(row["price_usd"])
        else:
            # Fallback 2: global estimate.
            pricing_source = "global_fallback"
            pricing_uncertain = True
            gross_cost = float(GLOBAL_FALLBACK_PRICES.get(test_name, 75.0))
            uncertainty_type = PRICING_UNAVAILABLE

        coverage = _normalize_coverage(insurance_coverage)
        net_cost = round(gross_cost * (1.0 - coverage), 2)

        result = CostLookupResult(
            test_name=test_name,
            country=normalized_country,
            city=normalized_city,
            gross_cost_usd=round(gross_cost, 2),
            insurance_coverage_pct=coverage,
            net_cost_usd=net_cost,
            pricing_source=pricing_source,
            pricing_uncertain=pricing_uncertain,
            uncertainty_type=uncertainty_type,
        )
        return {
            "test_name": result.test_name,
            "country": result.country,
            "city": result.city,
            "gross_cost_usd": result.gross_cost_usd,
            "insurance_coverage_pct": result.insurance_coverage_pct,
            "net_cost_usd": result.net_cost_usd,
            "pricing_source": result.pricing_source,
            "pricing_uncertain": result.pricing_uncertain,
            "uncertainty_type": result.uncertainty_type,
        }
