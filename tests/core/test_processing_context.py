"""
Unit tests for DataProcessingContext class.

:hierarchy: [Tests | Core | DataProcessingContext]
:relates-to:
 - motivated_by: "Need comprehensive tests for DataProcessingContext"
 - implements: "test_suite: 'DataProcessingContext'"
 - uses: ["class: 'DataProcessingContext'"]

:contract:
 - pre: "DataProcessingContext class is importable"
 - post: "All DataProcessingContext functionality is tested"

:complexity: 3
"""

import pytest

from dashboard_lego.core.processing_context import DataProcessingContext


def test_context_creation_with_no_params():
    """Test creating context with no params."""
    # Act
    context = DataProcessingContext.from_params(None)

    # Assert
    assert context.preprocessing_params == {}
    assert context.filtering_params == {}
    assert context.raw_params == {}


def test_context_creation_with_empty_params():
    """Test creating context with empty params dict."""
    # Act
    context = DataProcessingContext.from_params({})

    # Assert
    assert context.preprocessing_params == {}
    assert context.filtering_params == {}
    assert context.raw_params == {}


def test_context_default_all_params_to_preprocessing():
    """Test that without classifier, all params go to preprocessing."""
    # Arrange
    params = {"param1": "value1", "param2": "value2"}

    # Act
    context = DataProcessingContext.from_params(params)

    # Assert
    assert context.preprocessing_params == params
    assert context.filtering_params == {}
    assert context.raw_params == params


def test_context_with_custom_classifier():
    """Test context with custom param classifier."""
    # Arrange
    params = {
        "preprocess_agg": "sum",
        "filter_category": "A",
        "preprocess_date": "2024-01-01",
        "filter_min_value": 10,
    }

    def classifier(key):
        return "filter" if key.startswith("filter_") else "preprocess"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert context.preprocessing_params == {
        "preprocess_agg": "sum",
        "preprocess_date": "2024-01-01",
    }
    assert context.filtering_params == {"filter_category": "A", "filter_min_value": 10}
    assert context.raw_params == params


def test_context_preserves_raw_params():
    """Test that raw_params always contains original input."""
    # Arrange
    params = {"a": 1, "b": 2, "c": 3}

    def classifier(key):
        return "filter" if key == "b" else "preprocess"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert context.raw_params == params
    assert context.raw_params is not params  # Should be a copy


def test_context_raw_params_is_copy():
    """Test that raw_params is a copy, not reference."""
    # Arrange
    params = {"a": 1}

    # Act
    context = DataProcessingContext.from_params(params)
    params["b"] = 2  # Modify original

    # Assert
    assert "b" not in context.raw_params


def test_context_classifier_returns_preprocess_by_default():
    """Test that non-'filter' classifier returns are treated as 'preprocess'."""
    # Arrange
    params = {"a": 1, "b": 2}

    def classifier(key):
        return "something_else" if key == "a" else "filter"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    # 'a' should go to preprocessing (non-'filter' return)
    assert "a" in context.preprocessing_params
    # 'b' should go to filtering
    assert "b" in context.filtering_params


def test_context_handles_classifier_exceptions():
    """Test that context handles classifier exceptions gracefully."""
    # Arrange
    params = {"good": 1, "bad": 2}

    def failing_classifier(key):
        if key == "bad":
            raise ValueError("Classifier error")
        return "filter"

    # Act
    context = DataProcessingContext.from_params(params, failing_classifier)

    # Assert - bad param should default to preprocessing on error
    assert "bad" in context.preprocessing_params
    assert "good" in context.filtering_params


def test_context_with_complex_param_types():
    """Test context with various parameter types."""
    # Arrange
    params = {
        "string": "value",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "none": None,
    }

    def classifier(key):
        return "filter" if key in ["string", "list"] else "preprocess"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert context.filtering_params == {"string": "value", "list": [1, 2, 3]}
    assert context.preprocessing_params == {
        "int": 42,
        "float": 3.14,
        "bool": True,
        "dict": {"nested": "value"},
        "none": None,
    }


def test_context_direct_instantiation():
    """Test direct instantiation of DataProcessingContext."""
    # Act
    context = DataProcessingContext(
        preprocessing_params={"a": 1},
        filtering_params={"b": 2},
        raw_params={"a": 1, "b": 2},
    )

    # Assert
    assert context.preprocessing_params == {"a": 1}
    assert context.filtering_params == {"b": 2}
    assert context.raw_params == {"a": 1, "b": 2}


def test_context_default_values():
    """Test that DataProcessingContext has proper default values."""
    # Act
    context = DataProcessingContext()

    # Assert
    assert context.preprocessing_params == {}
    assert context.filtering_params == {}
    assert context.raw_params == {}


def test_context_classifier_with_control_panel_prefix():
    """Test common pattern: classify control panel params as filters."""
    # Arrange
    params = {
        "control_panel-category": "A",
        "control_panel-min_price": 100,
        "init_param": "value",
    }

    def classifier(key):
        return "filter" if key.startswith("control_panel-") else "preprocess"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert context.filtering_params == {
        "control_panel-category": "A",
        "control_panel-min_price": 100,
    }
    assert context.preprocessing_params == {"init_param": "value"}


def test_context_empty_classifier_returns():
    """Test behavior when classifier returns empty string."""
    # Arrange
    params = {"a": 1}

    def classifier(key):
        return ""  # Empty string

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert - should default to preprocessing
    assert "a" in context.preprocessing_params


def test_context_classifier_case_sensitivity():
    """Test that classifier return value is case-sensitive."""
    # Arrange
    params = {"a": 1, "b": 2}

    def classifier(key):
        return "Filter" if key == "a" else "filter"  # Capital F

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    # 'Filter' (capital) should be treated as preprocessing
    assert "a" in context.preprocessing_params
    # 'filter' (lowercase) should be filtering
    assert "b" in context.filtering_params


def test_context_all_params_to_filter():
    """Test scenario where all params are classified as filters."""
    # Arrange
    params = {"a": 1, "b": 2, "c": 3}

    def classifier(key):
        return "filter"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert context.preprocessing_params == {}
    assert context.filtering_params == params
    assert context.raw_params == params


def test_context_with_many_params():
    """Test context with large number of params."""
    # Arrange
    params = {f"param_{i}": i for i in range(100)}

    def classifier(key):
        return "filter" if int(key.split("_")[1]) % 2 == 0 else "preprocess"

    # Act
    context = DataProcessingContext.from_params(params, classifier)

    # Assert
    assert len(context.preprocessing_params) == 50
    assert len(context.filtering_params) == 50
    assert len(context.raw_params) == 100
