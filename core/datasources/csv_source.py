"""
Concrete implementation of a DataSource for CSV files.

"""
from typing import Any, Dict, Optional
import pandas as pd

from core.datasource import BaseDataSource

class CsvDataSource(BaseDataSource):
    """
    A data source that loads data from a local CSV file.

    """
    def __init__(self, file_path: str, read_csv_options: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initializes the CsvDataSource.

        Args:
            file_path: The absolute or relative path to the CSV file.
            read_csv_options: A dictionary of options to pass to pandas.read_csv.
            **kwargs: Keyword arguments for the parent BaseDataSource (e.g., cache_ttl).

        """
        super().__init__(**kwargs)
        self.file_path = file_path
        self.read_csv_options = read_csv_options or {}

    def _load_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Loads the data from the CSV file into a pandas DataFrame.
        This method is called by the caching layer in the base class.

        """
        try:
            # params could be used here to format the file_path if needed
            return pd.read_csv(self.file_path, **self.read_csv_options)
        except FileNotFoundError:
            print(f"Error: The file was not found at {self.file_path}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred while reading the CSV file: {e}")
            return pd.DataFrame()

    def get_processed_data(self) -> pd.DataFrame:
        """
        Returns the loaded DataFrame.

        """
        if self._data is None:
            # Attempt to load data if it hasn't been loaded yet
            if not self.init_data():
                return pd.DataFrame() # Return empty frame if loading fails
        return self._data

    def get_kpis(self) -> Dict[str, Any]:
        """
        Returns an empty dictionary. Users should subclass to implement this.

        """
        return {}

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
            return f"CSV data loaded from {self.file_path}. Shape: {self._data.shape}"
        return "No data loaded."
