"""Shared fixtures, markers, helpers. [Test Architecture 1.7]"""
from pathlib import Path

import pytest
import yaml


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Root path to tests/fixtures/."""
    return FIXTURES_DIR


@pytest.fixture
def parquet_fixtures(fixtures_dir):
    """Path to tests/fixtures/parquet/."""
    return fixtures_dir / "parquet"


@pytest.fixture
def csv_fixtures(fixtures_dir):
    """Path to tests/fixtures/csv/."""
    return fixtures_dir / "csv"


@pytest.fixture
def config_fixtures(fixtures_dir):
    """Path to tests/fixtures/configs/."""
    return fixtures_dir / "configs"


@pytest.fixture
def tmp_config(tmp_path):
    """Factory fixture: builds a YAML config file in tmp_path, returns path."""
    def _make_config(data: dict) -> Path:
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return config_path
    return _make_config


@pytest.fixture
def run_comparison():
    """Invokes the comparison pipeline programmatically."""
    from proofmark.pipeline import run

    def _run(config_path: Path, lhs_path: Path, rhs_path: Path) -> dict:
        return run(config_path, lhs_path, rhs_path)

    return _run
