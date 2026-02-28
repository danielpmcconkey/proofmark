"""Config validation tests — BDD scenarios 53-63. [FSD Appendix A]"""
from pathlib import Path

import pytest
import yaml

from proofmark import ConfigError
from proofmark.config import (
    ComparisonConfig,
    ReaderType,
    ToleranceType,
    load_config,
)


class TestValidConfig:
    """Scenario 53: Valid YAML config parses without error [BR-6.1 through BR-6.5]"""

    def test_valid_parquet_config_parses(self, config_fixtures):
        config, raw = load_config(config_fixtures / "parquet_default.yaml")
        assert config.comparison_target == "test_parquet_default"
        assert config.reader == ReaderType.PARQUET

    def test_valid_csv_config_parses(self, config_fixtures):
        config, raw = load_config(config_fixtures / "csv_simple.yaml")
        assert config.comparison_target == "test_csv_simple"
        assert config.reader == ReaderType.CSV
        assert config.csv is not None
        assert config.csv.header_rows == 1
        assert config.csv.trailer_rows == 0

    def test_defaults_applied(self, config_fixtures):
        config, _ = load_config(config_fixtures / "parquet_default.yaml")
        assert config.encoding == "utf-8"
        assert config.threshold == 100.0
        assert config.excluded_columns == ()
        assert config.fuzzy_columns == ()

    def test_raw_dict_returned_for_report_echo(self, config_fixtures):
        _, raw = load_config(config_fixtures / "parquet_default.yaml")
        assert isinstance(raw, dict)
        assert raw["reader"] == "parquet"


class TestMissingRequiredField:
    """Scenario 54: Missing required field produces error [BR-6.6]"""

    def test_missing_reader_raises_config_error(self, config_fixtures):
        with pytest.raises(ConfigError, match="'reader' is a required field"):
            load_config(config_fixtures / "invalid_missing_reader.yaml")

    def test_missing_comparison_target_raises_config_error(self, config_fixtures):
        with pytest.raises(ConfigError, match="'comparison_target' is a required field"):
            load_config(config_fixtures / "invalid_missing_comparison_target.yaml")


class TestUnknownReaderType:
    """Scenario 55: Unknown reader type produces error [BR-3.6]"""

    def test_unknown_reader_raises_config_error(self, config_fixtures):
        with pytest.raises(ConfigError, match='"excel" is not a valid reader type'):
            load_config(config_fixtures / "invalid_unknown_reader.yaml")

    def test_error_lists_valid_types(self, config_fixtures):
        with pytest.raises(ConfigError) as exc_info:
            load_config(config_fixtures / "invalid_unknown_reader.yaml")
        assert '"csv"' in str(exc_info.value)
        assert '"parquet"' in str(exc_info.value)


class TestFuzzyMissingToleranceType:
    """Scenario 56: FUZZY column without tolerance_type produces error [BR-7.6]"""

    def test_missing_tolerance_type_raises(self, config_fixtures):
        with pytest.raises(ConfigError, match="tolerance_type.*required.*FUZZY"):
            load_config(config_fixtures / "invalid_fuzzy_no_tolerance_type.yaml")


class TestFuzzyMissingToleranceValue:
    """Scenario 57: FUZZY column without tolerance value produces error [BR-7.7]"""

    def test_missing_tolerance_value_raises(self, config_fixtures):
        with pytest.raises(ConfigError, match="tolerance.*required.*FUZZY"):
            load_config(config_fixtures / "invalid_fuzzy_no_tolerance_value.yaml")


class TestExcludedMissingReason:
    """Scenario 58: EXCLUDED column without reason produces error [BR-5.3, BR-6.6]"""

    def test_missing_reason_raises(self, config_fixtures):
        with pytest.raises(ConfigError, match="reason.*required.*EXCLUDED"):
            load_config(config_fixtures / "invalid_excluded_no_reason.yaml")


class TestFuzzyMissingReason:
    """Scenario 59: FUZZY column without reason produces error [BR-5.8, BR-6.6]"""

    def test_missing_reason_raises(self, config_fixtures):
        with pytest.raises(ConfigError, match="reason.*required.*FUZZY"):
            load_config(config_fixtures / "invalid_fuzzy_no_reason.yaml")


class TestDuplicateClassification:
    """Scenario 60: Column in both EXCLUDED and FUZZY produces error [BR-5.1]"""

    def test_duplicate_classification_raises(self, config_fixtures):
        with pytest.raises(ConfigError, match="appears in multiple classification"):
            load_config(config_fixtures / "invalid_duplicate_classification.yaml")


class TestThresholdOutOfRange:
    """Scenario 61: Threshold out of range produces error [BR-11.22, FSD-5.2.11]"""

    def test_threshold_above_100_raises(self, tmp_config):
        path = tmp_config({
            "comparison_target": "test",
            "reader": "parquet",
            "threshold": 101.0,
        })
        with pytest.raises(ConfigError, match="threshold.*between 0.0 and 100.0"):
            load_config(path)


class TestNegativeThreshold:
    """Scenario 62: Negative threshold produces error [BR-11.22, FSD-5.2.11]"""

    def test_negative_threshold_raises(self, tmp_config):
        path = tmp_config({
            "comparison_target": "test",
            "reader": "parquet",
            "threshold": -5.0,
        })
        with pytest.raises(ConfigError, match="threshold.*between 0.0 and 100.0"):
            load_config(path)


class TestNegativeTolerance:
    """Scenario 63: Negative FUZZY tolerance produces error [FSD-5.2.11a]"""

    def test_negative_tolerance_raises(self, tmp_config):
        path = tmp_config({
            "comparison_target": "test",
            "reader": "parquet",
            "columns": {
                "fuzzy": [{
                    "name": "balance",
                    "tolerance": -0.01,
                    "tolerance_type": "absolute",
                    "reason": "Rounding",
                }],
            },
        })
        with pytest.raises(ConfigError, match="tolerance.*>= 0.0"):
            load_config(path)


class TestConfigWithAllClassifications:
    """Additional: mixed config parses correctly"""

    def test_mixed_classifications_parse(self, config_fixtures):
        config, _ = load_config(config_fixtures / "mixed_classifications.yaml")
        assert len(config.excluded_columns) == 1
        assert config.excluded_columns[0].name == "run_id"
        assert len(config.fuzzy_columns) == 1
        assert config.fuzzy_columns[0].name == "interest_accrued"
        assert config.fuzzy_columns[0].tolerance == 0.01
        assert config.fuzzy_columns[0].tolerance_type == ToleranceType.ABSOLUTE
