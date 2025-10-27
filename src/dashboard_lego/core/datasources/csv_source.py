"""
CSV data source with built-in DataBuilder.

:hierarchy: [Core | DataSources | CsvDataSource]
:contract:
 - pre: "file_path to CSV provided"
 - post: "CSV loaded and cached"

:complexity: 2
"""

from typing import Any, Dict, Optional

import pandas as pd

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.exceptions import DataLoadError


class CsvDataBuilder(DataBuilder):
    """
    DataBuilder for CSV files.

    :hierarchy: [Core | DataSources | CsvDataBuilder]
    :contract:
     - pre: "file_path exists"
     - post: "Returns loaded DataFrame"
    """

    def __init__(
        self,
        file_path: str,
        read_csv_options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.read_csv_options = read_csv_options or {}

    def build(self, **params) -> pd.DataFrame:
        """Load CSV file."""
        self.logger.info(f"[CsvDataBuilder] Loading {self.file_path}")
        try:
            df = pd.read_csv(self.file_path, **self.read_csv_options)
            self.logger.info(f"[CsvDataBuilder] Loaded {len(df)} rows")
            return df
        except FileNotFoundError as e:
            self.logger.error(f"CSV file not found: {self.file_path}")
            raise DataLoadError(f"CSV file not found: {self.file_path}") from e
        except pd.errors.EmptyDataError as e:
            self.logger.error(f"CSV file is empty: {self.file_path}")
            raise DataLoadError(f"CSV file is empty: {self.file_path}") from e
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            raise DataLoadError(f"Failed to load CSV: {e}") from e


class CsvDataSource(DataSource):
    """
    CSV data source.

    :hierarchy: [Core | DataSources | CsvDataSource]
    :complexity: 2
    """

    def __init__(
        self,
        file_path: str,
        read_csv_options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize CSV datasource.

        Args:
            file_path: Path to CSV file
            read_csv_options: Options for pd.read_csv()
        """
        # Create builder
        builder = CsvDataBuilder(file_path, read_csv_options)

        # Pass to parent
        super().__init__(data_builder=builder, **kwargs)
