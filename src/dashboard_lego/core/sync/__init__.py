"""
Sync API submodule for dashboard_lego.

Contains all synchronous implementations of core components:
- DataSource: Synchronous data source with 2-stage pipeline
- DataBuilder: Synchronous data builder
- DataTransformer: Synchronous data transformer
- LambdaBuilder/LambdaTransformer: Synchronous lambda handlers

:hierarchy: [Core | Sync]
:relates-to:
 - motivated_by: "Separate sync API into dedicated submodule for symmetry with async submodule"
 - implements: "Sync API submodule"
"""

from dashboard_lego.core.data_builder import DataBuilder, DfHandler
from dashboard_lego.core.data_transformer import (
    ChainedTransformer,
    DataFilter,
    DataTransformer,
)
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.lambda_handlers import LambdaBuilder, LambdaTransformer

__all__ = [
    "DataSource",
    "DataBuilder",
    "DfHandler",
    "DataTransformer",
    "DataFilter",
    "ChainedTransformer",
    "LambdaBuilder",
    "LambdaTransformer",
]
