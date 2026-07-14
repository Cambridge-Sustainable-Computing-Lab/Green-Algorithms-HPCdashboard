import pytest
import pandas as pd
from ga_dashboard.backend.ga_tools import LogsDataProcessor
from tests import helpers

class TestGATools:

    @pytest.fixture(autouse=True)
    def setup(self, config_data):
        self.test_config = config_data
        self.processor = LogsDataProcessor(self.test_config)
        self.wm = self.processor.cluster_info["workload_manager"].lower()
    
    def test_summarise_data_none_empty_df(self):
        result = self.processor.summarise_data(None)
        assert result is None

    def test_summarise_data_empty_df(self):
        with pytest.raises(AttributeError):
            self.processor.summarise_data(pd.DataFrame())

    def test_valid_run(self, monkeypatch):
        processor = LogsDataProcessor(self.test_config)
        monkeypatch.setattr(processor, "process_and_store", lambda summary_stats: None) # Mocked process_and_store method to avoid actual database operations
        summary = processor.run()
        result = summary['userDaily']

        expected = pd.read_csv(f"tests/testdata/{self.wm}/summarised_user_daily.csv")
        expected = helpers.align_expected_dtypes(expected, result)

        pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected[result.columns].reset_index(drop=True),
            check_exact=False,
            rtol=1e-4,
                )

        