import pytest
import pandas as pd
from ga_dashboard.backend.ga_tools import LogsDataProcessor
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
        

        