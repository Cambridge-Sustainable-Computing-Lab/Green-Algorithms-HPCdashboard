import pytest
import copy
import pandas as pd
from pathlib import Path
from ga_dashboard.backend.ga_tools import LogsDataProcessor
from ga_dashboard.backend.helpers import utils
from tests import helpers

class TestGATools:
    """
    Test suite for validating the core functionalities of the LogsDataProcessor class in the ga_tools module.
    This class contains unit tests that ensure the correct behavior of data summarization and processing methods.
    """
    @pytest.fixture(autouse=True)
    def setup(self, config_data):
        """
        Runs automatically before every test in this class.
        Sets up test instances and configuration.
        """
        self.test_config = config_data
        self.processor = LogsDataProcessor(self.test_config)
        self.wm = self.processor.cluster_info["workload_manager"].lower()
    
    def test_summarise_data_none_empty_df(self):
        """
        Scenario: Test the summarise_data method with None
        """
        result = self.processor.summarise_data(None)
        assert result is None

    def test_summarise_data_empty_df(self):
        """
        Scenario: Test the summarise_data method with an empty DataFrame
        """
        with pytest.raises(AttributeError):
            self.processor.summarise_data(pd.DataFrame())

    def test_valid_run(self, monkeypatch):
        """
        Scenario: Test to run end-to-end processing and summarization of logs data.
        This test:
        1. Mocks the process_and_store method (using monkeypatch) to avoid actual database operations.
        2. Runs the LogsDataProcessor with the test configuration.
        3. Compares the output summary with expected results from a CSV file.
        """
        processor = LogsDataProcessor(self.test_config)
        monkeypatch.setattr(processor, "process_and_store", lambda summary_stats: None) # Mocked process_and_store method to avoid actual database operations
        summary = processor.run()
        result = summary['userDaily'] # Picking user-wise summarised logs

        expected = pd.read_csv(f"tests/testdata/{self.wm}/summarised_user_daily.csv")
        expected = helpers.align_expected_dtypes(expected, result)

        pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected[result.columns].reset_index(drop=True),
            check_exact=False,
            rtol=1e-4,
                )
        
    def test_input_mode_file(self, monkeypatch):
        """
        Scenario: input_mode == 'file' with a non-empty path should read logs via utils.read_file_bytes, not try to fetch via (mocked) sacked.
        This test:
        1. Mocks backend.helpers.utils to spy on 'read_file_bytes()' calls
        2. Asserts that the file is read and zero sacct calls are made
        """
        file_config = copy.deepcopy(self.test_config)
        file_config["input_mode"] = "file"
        file_config["input_log_file_path"] = f"tests/testdata/{self.wm}/mock_raw/one_line_sacct_output.txt"

        processor = LogsDataProcessor(file_config)

        original_read_file_bytes = utils.read_file_bytes
        read_file_calls = []
        def check_read_file_bytes_calls(path):
            read_file_calls.append(path)
            return original_read_file_bytes(path)

        monkeypatch.setattr(utils, "read_file_bytes", check_read_file_bytes_calls)

        sacct_calls = []
        monkeypatch.setattr(
            "ga_core.SacctClient.pull_logs_by_time",
            lambda *a, **kw: sacct_calls.append((a, kw)),
        )
        monkeypatch.setattr(processor, "process_and_store", lambda summary_stats: None)

        processor.run()

        assert read_file_calls == [file_config["input_log_file_path"]]
        assert sacct_calls == []

    def test_input_mode_sacct(self, monkeypatch):
        """
        Scenario: input_mode is not 'file' with an empty path - logs should be fetched via (mocked) sacct instead 
        This test:
        1. Mocks backend.helpers.utils to spy on 'read_file_bytes()' calls
        2. Mocks SacctClient.pull_logs_by_time() to return mock raw logs
        2. Runs the pipeline and checks that file wasn't read.
        """
        slurm_config = copy.deepcopy(self.test_config)
        slurm_config["input_mode"] = "sacct"
        slurm_config["input_log_file_path"] = ""

        # Pick valid sacct bytes from mock raw data
        mock_valid_logs_path = "tests/testdata/slurm/mock_raw/one_line_sacct_output.txt"
        path = Path(mock_valid_logs_path).resolve()
        mock_valid_logs = path.read_bytes()

        processor = LogsDataProcessor(slurm_config)

        read_file_calls = []
        monkeypatch.setattr(
            utils, "read_file_bytes",
            lambda path: read_file_calls.append(path),
        )
        monkeypatch.setattr(
            "ga_core.SacctClient.pull_logs_by_time",
            lambda *a, **kw: mock_valid_logs,
        )
        monkeypatch.setattr(processor, "process_and_store", lambda summary_stats: None)

        processor.run()

        assert read_file_calls == []