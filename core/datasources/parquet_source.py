"""
This module defines the ParquetDataSource for loading data from Parquet files.

"""
import pandas as pd

from core.datasource import BaseDataSource

class ParquetDataSource(BaseDataSource):
    """
    A data source for loading data from a Parquet file.

        :hierarchy: [Core | DataSources | ParquetDataSource]
        :relates-to:
          - motivated_by: "plan.md: Фаза 5.2 - ParquetDataSource"
          - implements: "datasource: 'ParquetDataSource'"
          - uses: ["class: 'BaseDataSource'"]

        :rationale: "A dedicated class for Parquet files provides a clean separation of concerns and is consistent with the existing datasource architecture."
        :contract:
          - pre: "The file_path must point to a valid Parquet file."
          - post: "The data is loaded into a pandas DataFrame."

    """

    def __init__(self, file_path: str, **kwargs):
        self.file_path = file_path
        super().__init__(**kwargs)

    def _load_data(self, params: dict) -> pd.DataFrame:
        """Loads data from the Parquet file."""
        return pd.read_parquet(self.file_path)

    def get_kpis(self) -> dict:
        return {}

    def get_filter_options(self, filter_name: str) -> list:
        return []

    def get_summary(self) -> str:
        return ""