"""Shared fixtures for every test in this project."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from aisets.llm.fake import FakeLLM

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def fake_llm() -> FakeLLM:
    """A fresh, unscripted FakeLLM. Script it with .queue_response()/.queue_json()
    or .add_rule() before use — an unscripted call raises a clear error."""
    return FakeLLM()


@pytest.fixture
def sample_tickets_path() -> Path:
    path = DATA_DIR / "tickets.json"
    assert path.exists(), "Run 'python data/seed_data.py' first (see docs/02-setup-windows.md)."
    return path


@pytest.fixture
def sample_log_path() -> Path:
    path = DATA_DIR / "app.log"
    assert path.exists(), "Run 'python data/seed_data.py' first."
    return path


@pytest.fixture
def sample_metrics_path() -> Path:
    path = DATA_DIR / "metrics.json"
    assert path.exists(), "Run 'python data/seed_data.py' first."
    return path


@pytest.fixture
def sample_runbooks_dir() -> Path:
    path = DATA_DIR / "runbooks"
    assert path.exists(), "Run 'python data/seed_data.py' first."
    return path


@pytest.fixture
def tmp_orders_db(tmp_path: Path) -> Path:
    """A throwaway copy of the seeded orders.db, so tests that write to it
    (order status changes, etc.) never touch the real sample data."""
    src = DATA_DIR / "orders.db"
    assert src.exists(), "Run 'python data/seed_data.py' first."
    dst = tmp_path / "orders.db"
    shutil.copy(src, dst)
    conn = sqlite3.connect(dst)
    conn.close()
    return dst
