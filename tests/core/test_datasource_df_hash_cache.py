import pandas as pd

from dashboard_lego.core.datasource import DataSource


class _TestBuilder:
    def __init__(self, logger=None):
        self.logger = logger

    def build(self, v: int = 0) -> pd.DataFrame:
        # Different 'v' produces different DataFrame content
        return pd.DataFrame({"val": [v, v + 1, v + 2]})


class _TestTransformer:
    def __init__(self, logger=None):
        self.logger = logger

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        # Identity transform to let Stage 2 cache be exercised
        return data


def test_stage2_cache_key_includes_built_data_content(tmp_path):
    ds = DataSource(
        data_builder=_TestBuilder(),
        data_transformer=_TestTransformer(),
        cache_dir=str(tmp_path),
    )

    # First call with v=10
    df1 = ds.get_processed_data({"build__v": 10})
    assert list(df1["val"]) == [10, 11, 12]

    # Second call with different built content but SAME transform params
    # If Stage 2 cache key ignored built content, we could get df1 cached value
    df2 = ds.get_processed_data({"build__v": 100})
    assert list(df2["val"]) == [100, 101, 102]

    # Third call back to v=10 should return original content (cache hit is fine)
    df3 = ds.get_processed_data({"build__v": 10})
    assert list(df3["val"]) == [10, 11, 12]
