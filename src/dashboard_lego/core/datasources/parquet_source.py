"""
This module defines the ParquetDataSource for loading data from Parquet files.

"""

import pandas as pd

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.exceptions import DataLoadError
from dashboard_lego.utils.logger import get_logger


class ParquetDataSource(BaseDataSource):
    """
    A data source for loading data from a Parquet file.

        :hierarchy: [Core | DataSources | ParquetDataSource]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Parquet format provides efficient
            columnar storage for large datasets with better compression"
          - implements: "datasource: 'ParquetDataSource'"
          - uses: ["class: 'BaseDataSource'"]

        :rationale: "A dedicated class for Parquet files provides a clean separation of concerns and is consistent with the existing datasource architecture."
        :contract:
          - pre: "The file_path must point to a valid Parquet file."
          - post: "The data is loaded into a pandas DataFrame."

    """

    def __init__(self, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(__name__, ParquetDataSource)
        self.file_path = file_path

        self.logger.info(f"Parquet datasource initialized for file: {file_path}")

    def _load_data(self, params: dict) -> pd.DataFrame:
        """Loads data from the Parquet file, applying column selection and filters."""
        self.logger.debug(f"Loading Parquet data from: {self.file_path}")

        try:
            columns = params.get("columns")
            self.logger.debug(f"Column selection: {columns}")

            df = pd.read_parquet(self.file_path, columns=columns)
            self.logger.info(
                f"Parquet loaded successfully: {len(df)} rows, "
                f"{len(df.columns)} columns"
            )

            if df.empty:
                self.logger.warning("Parquet file is empty")
                return df

            filters = params.get("filters")
            if filters:
                self.logger.debug(f"Applying {len(filters)} filters")
                for i, f in enumerate(filters):
                    if f:
                        self.logger.debug(f"Applying filter {i+1}: {f}")
                        df = df.query(f)
                        self.logger.debug(f"After filter {i+1}: {len(df)} rows")

            self.logger.info(
                f"Final dataset: {len(df)} rows, {len(df.columns)} columns"
            )
            return df

        except FileNotFoundError as e:
            self.logger.error(f"Parquet file not found: {self.file_path}")
            raise DataLoadError(f"Parquet file not found: {self.file_path}") from e
        except Exception as e:
            self.logger.error(f"Error loading Parquet: {e}", exc_info=True)
            raise DataLoadError(
                f"Failed to load Parquet from {self.file_path}: {e}"
            ) from e

    def get_kpis(self) -> dict:
        return {}

    def get_filter_options(self, filter_name: str) -> list:
        return []

    def get_summary(self) -> str:
        if self._data is not None and not self._data.empty:
            summary = (
                f"Parquet data loaded from {self.file_path}. "
                f"Shape: {self._data.shape}"
            )
            self.logger.debug(f"Generated summary: {summary}")
            return summary
        self.logger.debug("No data loaded for summary")
        return "No data loaded."
