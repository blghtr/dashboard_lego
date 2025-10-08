"""
Concrete implementation of a DataSource for CSV files.

"""

from typing import Any, Dict, List, Optional

import pandas as pd

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.exceptions import DataLoadError
from dashboard_lego.utils.logger import get_logger


class CsvDataSource(BaseDataSource):
    """
    A data source that loads data from a local CSV file.

    """

    def __init__(
        self,
        file_path: str,
        read_csv_options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initializes the CsvDataSource.

        Args:
            file_path: The absolute or relative path to the CSV file.
            read_csv_options: A dictionary of options to pass to
                             pandas.read_csv.
            **kwargs: Keyword arguments for the parent BaseDataSource
                     (e.g., cache_ttl).

        """
        super().__init__(**kwargs)
        self.logger = get_logger(__name__, CsvDataSource)
        self.file_path = file_path
        self.read_csv_options = read_csv_options or {}

        self.logger.info(f"CSV datasource initialized for file: {file_path}")
        self.logger.debug(f"Read options: {self.read_csv_options}")

    def _load_raw_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Load raw data from CSV file (NO filtering).

        :hierarchy: [Core | DataSources | CsvDataSource | Load Stage]
        :relates-to:
         - motivated_by: "Refactor: Separate data loading from filtering"
         - implements: "method: '_load_raw_data'"

        :contract:
         - pre: "file_path points to valid CSV file"
         - post: "Returns raw DataFrame from CSV"
         - invariant: "Does NOT apply filters"

        Args:
            params: Parameters for CSV loading (not used for filtering).
                   Reserved for future use (e.g., column selection).

        Returns:
            Raw DataFrame from CSV file

        Raises:
            DataLoadError: If file not found or loading fails

        Note:
            Filtering logic has been removed and should be handled by DataFilter.
            This method only loads the raw CSV data.
        """
        self.logger.debug(f"Loading raw CSV data from: {self.file_path}")

        try:
            df = pd.read_csv(self.file_path, **self.read_csv_options)
            self.logger.info(
                f"CSV loaded successfully: {len(df)} rows, "
                f"{len(df.columns)} columns"
            )

            if df.empty:
                self.logger.warning("CSV file is empty")

            return df

        except FileNotFoundError as e:
            self.logger.error(f"CSV file not found: {self.file_path}")
            raise DataLoadError(f"CSV file not found: {self.file_path}") from e
        except pd.errors.EmptyDataError as e:
            self.logger.error(f"CSV file is empty: {self.file_path}")
            raise DataLoadError(f"CSV file is empty: {self.file_path}") from e
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}", exc_info=True)
            raise DataLoadError(f"Failed to load CSV from {self.file_path}: {e}") from e

    def get_kpis(self) -> Dict[str, Any]:
        """
        Returns KPI values calculated from the loaded data.

        """
        if self._data is None or self._data.empty:
            return {}

        kpis = {}

        # Calculate total sales if Sales column exists
        if "Sales" in self._data.columns:
            kpis["total_sales"] = self._data["Sales"].sum()

        # Calculate total units if UnitsSold column exists
        if "UnitsSold" in self._data.columns:
            kpis["total_units"] = self._data["UnitsSold"].sum()

        # Calculate average price if both Sales and UnitsSold exist
        if "Sales" in self._data.columns and "UnitsSold" in self._data.columns:
            # Avoid division by zero
            total_units = self._data["UnitsSold"].sum()
            if total_units > 0:
                kpis["avg_price"] = self._data["Sales"].sum() / total_units
            else:
                kpis["avg_price"] = 0

        return kpis

    def get_filter_options(self, filter_name: str) -> List[Dict[str, Any]]:
        """
        Returns an empty list. Users should subclass to implement this.

        """
        return []

    def get_summary(self) -> str:
        """
        Returns a basic summary of the loaded data.

        """
        if self._data is not None and not self._data.empty:
            summary = (
                f"CSV data loaded from {self.file_path}. " f"Shape: {self._data.shape}"
            )
            self.logger.debug(f"Generated summary: {summary}")
            return summary
        self.logger.debug("No data loaded for summary")
        return "No data loaded."
