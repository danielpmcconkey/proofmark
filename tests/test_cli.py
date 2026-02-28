"""CLI tests — BDD scenarios 48-52. [FSD Appendix A]"""
import json

import pytest


@pytest.mark.cli
class TestExitCode0OnPass:
    """Scenario 48: Exit code 0 on PASS [BR-12.6]"""

    def test_pass_returns_exit_0(self, run_cli, parquet_fixtures, config_fixtures):
        code, stdout, stderr = run_cli(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "identical_simple" / "lhs",
            parquet_fixtures / "identical_simple" / "rhs",
        )
        assert code == 0
        report = json.loads(stdout)
        assert report["summary"]["result"] == "PASS"


@pytest.mark.cli
class TestExitCode1OnFail:
    """Scenario 49: Exit code 1 on FAIL [BR-12.7]"""

    def test_fail_returns_exit_1(self, run_cli, parquet_fixtures, config_fixtures):
        code, stdout, stderr = run_cli(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "data_mismatch" / "lhs",
            parquet_fixtures / "data_mismatch" / "rhs",
        )
        assert code == 1
        report = json.loads(stdout)
        assert report["summary"]["result"] == "FAIL"


@pytest.mark.cli
class TestExitCode1OnSchemaFail:
    """F-01: Schema mismatch produces exit code 1 (FAIL, not ERROR) at CLI level [BR-4.9]"""

    def test_schema_mismatch_returns_exit_1(self, run_cli, parquet_fixtures, config_fixtures):
        code, stdout, stderr = run_cli(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "schema_mismatch_column_count" / "lhs",
            parquet_fixtures / "schema_mismatch_column_count" / "rhs",
        )
        assert code == 1
        report = json.loads(stdout)
        assert report["summary"]["result"] == "FAIL"
        assert report["mismatches"]["schema_mismatches"] is not None
        assert len(report["mismatches"]["schema_mismatches"]) >= 1


@pytest.mark.cli
class TestExitCode2OnError:
    """Scenario 50: Exit code 2 on error [BR-12.8]"""

    def test_missing_path_returns_exit_2(self, run_cli, config_fixtures, tmp_path):
        code, stdout, stderr = run_cli(
            config_fixtures / "parquet_default.yaml",
            tmp_path / "nonexistent",
            tmp_path / "also_nonexistent",
        )
        assert code == 2
        assert "Error" in stderr
        # No JSON report on error — stdout must be empty
        assert stdout.strip() == ""

    def test_invalid_config_returns_exit_2(self, run_cli, parquet_fixtures, config_fixtures):
        code, stdout, stderr = run_cli(
            config_fixtures / "invalid_missing_reader.yaml",
            parquet_fixtures / "identical_simple" / "lhs",
            parquet_fixtures / "identical_simple" / "rhs",
        )
        assert code == 2


@pytest.mark.cli
class TestOutputToFile:
    """Scenario 51: Output to file with --output flag [BR-12.4]"""

    def test_output_written_to_file(self, run_cli, parquet_fixtures, config_fixtures, tmp_path):
        output_path = tmp_path / "report.json"
        code, stdout, stderr = run_cli(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "identical_simple" / "lhs",
            parquet_fixtures / "identical_simple" / "rhs",
            output_path=output_path,
        )
        assert code == 0
        assert output_path.exists()
        report = json.loads(output_path.read_text())
        assert report["summary"]["result"] == "PASS"
        # stdout should be empty when --output is used
        assert stdout.strip() == ""


@pytest.mark.cli
class TestExitCode2OnEncodingError:
    """H-06: Encoding error produces exit code 2 at CLI level [BR-9.2, BR-12.8]"""

    def test_encoding_error_returns_exit_2(self, run_cli, csv_fixtures, config_fixtures):
        code, stdout, stderr = run_cli(
            config_fixtures / "csv_encoding_ascii.yaml",
            csv_fixtures / "encoding_invalid" / "lhs.csv",
            csv_fixtures / "encoding_invalid" / "rhs.csv",
        )
        assert code == 2
        assert "Error" in stderr
        assert "encoding" in stderr.lower() or "decode" in stderr.lower()
        assert stdout.strip() == ""


@pytest.mark.cli
class TestExitCode2OnNonNumericFuzzy:
    """F-03: Non-numeric FUZZY column produces exit code 2 at CLI level [BR-4.21, BR-12.8]"""

    def test_string_fuzzy_returns_exit_2(self, run_cli, parquet_fixtures, tmp_config):
        config_path = tmp_config({
            "comparison_target": "test_non_numeric_fuzzy",
            "reader": "parquet",
            "columns": {
                "fuzzy": [{
                    "name": "name",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Name is a string — should fail",
                }],
            },
        })
        code, stdout, stderr = run_cli(
            config_path,
            parquet_fixtures / "identical_simple" / "lhs",
            parquet_fixtures / "identical_simple" / "rhs",
        )
        assert code == 2
        assert "Error" in stderr
        assert stdout.strip() == ""


@pytest.mark.cli
class TestConfigRequired:
    """Scenario 52: Config flag is required [BR-12.1]"""

    def test_missing_config_returns_exit_2(self, tmp_path):
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "proofmark", "compare"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2

    def test_no_subcommand_returns_exit_2(self):
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "proofmark"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2
        # Usage text goes to stdout via print_help(), no JSON report
        assert "usage:" in result.stdout.lower()
