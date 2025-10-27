#!/usr/bin/env python3
"""
Test script for placeholder resolution fix.

Tests both standalone and inline placeholder resolution in plot_kwargs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard_lego', 'src'))

import pandas as pd
from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.data_builder import DataBuilder

# Test data
df = pd.DataFrame({
    'session_length': [10, 20, 30, 40, 50],
    'max_idle': [5, 10, 15, 20, 25],
    'metric_selector': ['Premium', 'Standard', 'Premium', 'Basic', 'Standard']
})

class TestDataBuilder(DataBuilder):
    def build(self, params=None):
        return df

# Create datasource
datasource = DataSource(data_builder=TestDataBuilder())

print("🧪 Testing Placeholder Resolution Fix")
print("=" * 50)

# Test 1: Inline placeholder in title (the reported issue)
print("\n1. Testing inline placeholder in title:")
chart1 = TypedChartBlock(
    block_id="test_chart",
    datasource=datasource,
    plot_type="scatter",
    plot_params={"x": "session_length", "y": "max_idle"},
    plot_kwargs={
        "title": "Session Length vs Max Idle (colored by {{metric_selector}})"
    }
)

# Simulate control values
control_values = {"metric_selector": "Premium"}

# Test the helper function directly
resolved_title = chart1._resolve_string_placeholders(
    "Session Length vs Max Idle (colored by {{metric_selector}})",
    control_values
)

print(f"   Original: Session Length vs Max Idle (colored by {{metric_selector}})")
print(f"   Resolved: {resolved_title}")
print(f"   ✅ Expected: Session Length vs Max Idle (colored by Premium)")
print(f"   ✅ Match: {resolved_title == 'Session Length vs Max Idle (colored by Premium)'}")

# Test 2: Standalone placeholder (existing functionality)
print("\n2. Testing standalone placeholder:")
resolved_standalone = chart1._resolve_string_placeholders(
    "{{metric_selector}}",
    control_values
)
print(f"   Original: {{metric_selector}}")
print(f"   Resolved: {resolved_standalone}")
print(f"   ✅ Expected: Premium")
print(f"   ✅ Match: {resolved_standalone == 'Premium'}")

# Test 3: Multiple placeholders in same string
print("\n3. Testing multiple placeholders:")
control_values_multi = {"metric_selector": "Premium", "color": "blue"}
resolved_multi = chart1._resolve_string_placeholders(
    "Chart: {{metric_selector}} data in {{color}}",
    control_values_multi
)
print(f"   Original: Chart: {{metric_selector}} data in {{color}}")
print(f"   Resolved: {resolved_multi}")
print(f"   ✅ Expected: Chart: Premium data in blue")
print(f"   ✅ Match: {resolved_multi == 'Chart: Premium data in blue'}")

# Test 4: Non-string value (should pass through)
print("\n4. Testing non-string value:")
resolved_non_string = chart1._resolve_string_placeholders(42, control_values)
print(f"   Original: 42")
print(f"   Resolved: {resolved_non_string}")
print(f"   ✅ Expected: 42")
print(f"   ✅ Match: {resolved_non_string == 42}")

# Test 5: Unresolved placeholder (should log warning and return empty)
print("\n5. Testing unresolved placeholder:")
resolved_unresolved = chart1._resolve_string_placeholders(
    "Text with {{unknown_control}}",
    control_values
)
print(f"   Original: Text with {{unknown_control}}")
print(f"   Resolved: {resolved_unresolved}")
print(f"   ✅ Expected: Text with ")
print(f"   ✅ Match: {resolved_unresolved == 'Text with '}")

print("\n" + "=" * 50)
print("🎉 All tests completed!")
print("\nThe fix should now resolve inline placeholders in title strings like:")
print('   title: "Session Length vs Max Idle (colored by {{metric_selector}})"')
print("   → 'Session Length vs Max Idle (colored by Premium)'")
