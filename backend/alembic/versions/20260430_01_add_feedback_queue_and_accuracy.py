"""Add override, accuracy tracking, and feedback queue tables.

Revision ID: 20260430_01
Revises:
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260430_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.execute("ALTER TABLE disease_rankings ADD COLUMN confirmed_by_doctor INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE recommended_tests ADD COLUMN doctor_confirmed INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feedback_queue")
    op.execute("DROP TABLE IF EXISTS ai_accuracy_tracking")
    op.execute("DROP TABLE IF EXISTS doctor_overrides")
