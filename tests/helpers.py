from datetime import date
import pandas as pd


def align_expected_dtypes(expected: pd.DataFrame, result: pd.DataFrame) -> pd.DataFrame:
    """
    Loading CSV files loses dtype info - every column comes back as a string. 
    For any column that `result` actually holds as a date/datetime,
    convert the matching `expected` column (read from CSV) to line up.

    :param expected: DataFrame read from CSV file
    :param result: DataFrame produced by the code under test
    :return: expected DataFrame with dtypes aligned to result DataFrame
    """
    expected = expected.copy()

    for col in expected.columns:
        if col not in result.columns:
            continue

        result_col = result[col]

        if pd.api.types.is_datetime64_any_dtype(result_col):
            expected[col] = pd.to_datetime(expected[col])
        elif pd.api.types.is_timedelta64_dtype(result_col):
            expected[col] = pd.to_timedelta(expected[col])
        elif result_col.dropna().apply(lambda v: isinstance(v, date)).all() and not result_col.dropna().empty:
            expected[col] = pd.to_datetime(expected[col]).dt.date

    return expected