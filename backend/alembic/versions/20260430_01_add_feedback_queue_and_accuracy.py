"""Add override, accuracy tracking, and feedback queue tables.

Revision ID: 20260430_01
Revises:
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op
from sqlalchemy.exc import OperationalError

# revision identifiers, used by Alembic.
revision = "20260430_01"
down_revision = None
branch_labels = None
depends_on = None


def _safe_execute(sql: str) -> None:
    try:
        op.execute(sql)
    except OperationalError:
        pass


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            medical_history TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            chief_complaint TEXT NOT NULL DEFAULT '',
            symptoms TEXT NOT NULL DEFAULT '',
            clinical_summary TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS disease_test_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL,
            test_name TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 3),
            clinical_reason TEXT NOT NULL,
            guideline_reference TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(disease_name, test_name)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS disease_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            disease_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            supporting_symptoms TEXT NOT NULL DEFAULT '',
            clinical_basis TEXT NOT NULL DEFAULT '',
            confirmed_by_doctor INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recommended_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 3),
            source_disease TEXT NOT NULL,
            disease_confidence REAL NOT NULL,
            clinical_reason TEXT NOT NULL,
            guideline_reference TEXT NOT NULL,
            recommendation_reason TEXT NOT NULL,
            uncertainty_type TEXT,
            doctor_confirmed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS country_test_pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            city TEXT,
            test_name TEXT NOT NULL,
            price_usd REAL NOT NULL CHECK(price_usd >= 0),
            source_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(country, city, test_name)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS burden_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            duration_days INTEGER NOT NULL,
            frequency_count INTEGER NOT NULL,
            severity_score REAL NOT NULL,
            raw_burden REAL NOT NULL,
            normalized_score REAL NOT NULL,
            category TEXT NOT NULL,
            explanation TEXT NOT NULL,
            ordering_snapshot TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS visit_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            vital_name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            normal_min REAL,
            normal_max REAL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS doctor_overrides (
            override_id TEXT PRIMARY KEY,
            visit_id INTEGER NOT NULL,
            doctor_id TEXT NOT NULL,
            confirmed_disease TEXT NOT NULL,
            confirmed_tests TEXT NOT NULL DEFAULT '[]',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_accuracy_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL UNIQUE,
            override_id TEXT NOT NULL,
            top1_match REAL NOT NULL,
            top3_match REAL NOT NULL,
            test_overlap REAL NOT NULL,
            severity_delta REAL NOT NULL,
            burden_delta REAL NOT NULL,
            composite_score REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_queue (
            queue_id TEXT PRIMARY KEY,
            visit_id INTEGER NOT NULL,
            override_id TEXT NOT NULL,
            feature_vector TEXT NOT NULL,
            label_disease TEXT NOT NULL,
            label_tests TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            consumed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            report_path TEXT NOT NULL,
            download_url TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    _safe_execute("ALTER TABLE visits ADD COLUMN patient_id INTEGER")
    _safe_execute("ALTER TABLE visits ADD COLUMN chief_complaint TEXT NOT NULL DEFAULT ''")
    _safe_execute("ALTER TABLE visits ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
    _safe_execute("ALTER TABLE visits ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
    _safe_execute("ALTER TABLE disease_rankings ADD COLUMN confirmed_by_doctor INTEGER NOT NULL DEFAULT 0")
    _safe_execute("ALTER TABLE recommended_tests ADD COLUMN doctor_confirmed INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feedback_queue")
    op.execute("DROP TABLE IF EXISTS ai_accuracy_tracking")
    op.execute("DROP TABLE IF EXISTS doctor_overrides")
