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

    def _load_raw_data(self, params: dict) -> pd.DataFrame:
        """
        Load raw data from Parquet file (NO filtering).

        :hierarchy: [Core | DataSources | ParquetDataSource | Load Stage]
        :relates-to:
         - motivated_by: "Refactor: Separate data loading from filtering"
         - implements: "method: '_load_raw_data'"

        :contract:
         - pre: "file_path points to valid Parquet file"
         - post: "Returns raw DataFrame from Parquet"
         - invariant: "Does NOT apply filters"

        Args:
            params: Parameters for Parquet loading (e.g., column selection).
                   Can include 'columns' for selective column loading.

        Returns:
            Raw DataFrame from Parquet file

        Raises:
            DataLoadError: If file not found or loading fails

        Note:
            Filtering logic has been removed and should be handled by DataFilter.
            Column selection is still supported as it affects data loading performance.
        """
        self.logger.debug(f"Loading raw Parquet data from: {self.file_path}")

        try:
            columns = params.get("columns")
            if columns:
                self.logger.debug(f"Column selection: {columns}")

            df = pd.read_parquet(self.file_path, columns=columns)
            self.logger.info(
                f"Parquet loaded successfully: {len(df)} rows, "
                f"{len(df.columns)} columns"
            )

            if df.empty:
                self.logger.warning("Parquet file is empty")

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
