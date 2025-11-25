"""
Parquet data source with built-in DataBuilder.

:hierarchy: [Core | DataSources | ParquetDataSource]
:contract:
 - pre: "file_path to Parquet provided"
 - post: "Parquet loaded and cached"

:complexity: 2
"""

import pandas as pd

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.exceptions import DataLoadError


class ParquetDataBuilder(DataBuilder):
    """
    DataBuilder for Parquet files.

    :hierarchy: [Core | DataSources | ParquetDataBuilder]
    :contract:
     - pre: "file_path exists"
     - post: "Returns loaded DataFrame"
    """

    def __init__(self, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path

    def _build(self, **kwargs) -> pd.DataFrame:
        """Load Parquet file."""
        self.logger.info(f"[ParquetDataBuilder] Loading {self.file_path}")
        try:
            # Support column selection for performance
            columns = kwargs.get("columns")
            df = pd.read_parquet(self.file_path, columns=columns)
            self.logger.info(f"[ParquetDataBuilder] Loaded {len(df)} rows")
            return df
        except FileNotFoundError as e:
            self.logger.error(f"Parquet file not found: {self.file_path}")
            raise DataLoadError(f"Parquet file not found: {self.file_path}") from e
        except Exception as e:
            self.logger.error(f"Error loading Parquet: {e}")
            raise DataLoadError(f"Failed to load Parquet: {e}") from e


class ParquetDataSource(DataSource):
    """
    Parquet data source.

    :hierarchy: [Core | DataSources | ParquetDataSource]
    :complexity: 2
    """

    def __init__(self, file_path: str, **kwargs):
        """
        Initialize Parquet datasource.

        Args:
            file_path: Path to Parquet file
        """
        # Create builder
        builder = ParquetDataBuilder(file_path)

        # Pass to parent
        super().__init__(data_builder=builder, **kwargs)
