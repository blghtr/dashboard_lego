"""
Base preset class for TypedChartBlock with flexible control configuration.

Abstract base class providing standardized control configuration pattern
for all TypedChartBlock presets.

:hierarchy: [Presets | Base | BasePreset]
:relates-to:
 - motivated_by: "Standardized preset development pattern for consistency and maintainability"
 - implements: "abstract class: 'BasePreset'"
 - uses: ["block: 'TypedChartBlock'"]

:contract:
 - pre: "Subclass must implement default_controls property and plot_type"
 - post: "Provides flexible control configuration via controls parameter"
 - controls_logic: "controls=False: no controls, controls=True: default controls, controls=dict: custom control config"

:complexity: 5
:decision_cache: "Abstract base class pattern for consistent preset development"
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core.datasource import DataSource


class BasePreset(TypedChartBlock, ABC):
    """
    Abstract base class for TypedChartBlock presets with flexible control configuration.

    :hierarchy: [Presets | Base | BasePreset]
    :relates-to:
     - motivated_by: "Standardized preset development pattern for consistency and maintainability"
     - implements: "abstract class: 'BasePreset'"
     - uses: ["block: 'TypedChartBlock'"]

    :contract:
     - pre: "Subclass must implement default_controls property and plot_type"
     - post: "Provides flexible control configuration via controls parameter"
     - controls_logic: "controls=False: no controls, controls=True: default controls, controls=dict: custom control config"

    :complexity: 5
    :decision_cache: "Abstract base class pattern for consistent preset development"

    This class provides a standardized pattern for creating TypedChartBlock presets
    with flexible control configuration. Subclasses must implement:

    1. `default_controls` property: Dict of default Control objects
    2. `plot_type` property: String plot type from registry
    3. `_build_plot_params()` method: Build plot_params based on available controls
    4. `_build_plot_kwargs()` method: Build plot_kwargs based on available controls
    5. `_get_plot_title()` method: Return dynamic plot title or None

    Usage:
        ```python
        class MyPreset(BasePreset):
            @abstractproperty
            def default_controls(self) -> Dict[str, Control]:
                return {
                    "param1": Control(component=dcc.Dropdown, props={...}),
                    "param2": Control(component=dbc.Switch, props={...}),
                }

            @abstractproperty
            def plot_type(self) -> str:
                return "my_plot_type"

            def _build_plot_params(self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]) -> Dict[str, Any]:
                plot_params = {}
                if "param1" in final_controls:
                    plot_params["param1"] = "{{param1}}"
                else:
                    plot_params["param1"] = kwargs.get("param1", "default_value")
                return plot_params

            def _build_plot_kwargs(self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]) -> Dict[str, Any]:
                plot_kwargs = {}
                if "param2" in final_controls:
                    plot_kwargs["param2"] = "{{param2}}"
                else:
                    plot_kwargs["param2"] = kwargs.get("param2", False)
                return plot_kwargs

            def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
                if "param1" in final_controls:
                    return "My Plot: {{param1}}"
                return None
        ```
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to=None,
        title: str = "Preset Chart",
        controls: Union[bool, Dict[str, Union[bool, Control]]] = False,
        **kwargs,
    ):
        """
        Initialize preset with flexible control configuration.

        :hierarchy: [Presets | Base | BasePreset | Initialization]
        :relates-to:
         - motivated_by: "Flexible preset initialization with configurable controls"
         - implements: "method: '__init__'"

        :contract:
         - pre: "datasource meets requirements, subclass implements required properties/methods"
         - post: "Preset ready with configured controls or no controls"
         - controls_logic: "controls=False: no controls, controls=True: default controls, controls=dict: custom control config"

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            controls: Control configuration:
                - False (default): No controls, expects values in kwargs
                - True: Create default controls for all parameters
                - Dict[str, bool|Control]: Custom control configuration:
                    - bool: Enable/disable default control
                    - Control: Replace with custom control
            **kwargs: Additional styling parameters and control values
        """
        # Validate datasource requirements (subclass can override)
        self._validate_datasource(datasource)

        # Get default controls from subclass
        default_controls = self.default_controls

        # Process controls parameter
        final_controls = self._process_controls_parameter(
            controls, default_controls, block_id
        )

        # Build plot parameters using subclass methods
        plot_params = self._build_plot_params(final_controls, kwargs)
        plot_kwargs = self._build_plot_kwargs(final_controls, kwargs)
        plot_title = self._get_plot_title(final_controls)

        # Initialize parent class
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            plot_type=self._get_plot_type(),
            plot_params=plot_params,
            plot_kwargs=plot_kwargs,
            plot_title=plot_title,
            title=title,
            controls=final_controls,
            subscribes_to=subscribes_to,
            **kwargs,
        )

    @property
    @abstractmethod
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for this preset.

        :hierarchy: [Presets | Base | BasePreset | DefaultControls]
        :relates-to:
         - motivated_by: "Subclass must define available controls"
         - implements: "abstract property: 'default_controls'"

        :contract:
         - pre: "Subclass implementation"
         - post: "Returns dict of Control objects with default configurations"

        Returns:
            Dictionary mapping control names to Control objects
        """
        pass

    @abstractmethod
    def _get_plot_type(self) -> str:
        """
        Abstract method to get plot type from subclass.

        This method must be implemented by subclasses.

        :hierarchy: [Presets | Base | BasePreset | PlotType]
        :relates-to:
         - motivated_by: "Subclass must specify plot type"
         - implements: "abstract method: '_get_plot_type'"

        :contract:
         - pre: "Subclass implementation"
         - post: "Returns string plot type that exists in PLOT_REGISTRY"

        Returns:
            Plot type string (e.g., "knee_plot", "histogram")
        """
        pass

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements.

        :hierarchy: [Presets | Base | BasePreset | Validation]
        :relates-to:
         - motivated_by: "Ensure datasource meets preset requirements"
         - implements: "method: '_validate_datasource'"

        :contract:
         - pre: "datasource is DataSource instance"
         - post: "Raises ValueError if requirements not met, otherwise passes"

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't meet requirements
        """
        # Default implementation - subclasses can override
        df = datasource.get_processed_data()
        if df.empty:
            raise ValueError("Datasource contains no data")

    def _process_controls_parameter(
        self,
        controls: Union[bool, Dict[str, Union[bool, Control]]],
        default_controls: Dict[str, Control],
        block_id: str,
    ) -> Dict[str, Control]:
        """
        Process controls parameter into final control configuration.

        :hierarchy: [Presets | Base | BasePreset | ControlProcessing]
        :relates-to:
         - motivated_by: "Standardized control parameter processing"
         - implements: "method: '_process_controls_parameter'"

        :contract:
         - pre: "controls is bool or dict, default_controls is dict of Controls"
         - post: "Returns final control configuration dict"

        Args:
            controls: Control configuration parameter
            default_controls: Default control definitions
            block_id: Block ID for control ID generation

        Returns:
            Final control configuration dictionary

        Raises:
            ValueError: If controls parameter is invalid
        """
        final_controls = {}

        if controls is True:
            # Use all default controls
            final_controls = default_controls.copy()
        elif isinstance(controls, dict):
            # Custom control configuration
            for control_name, control_config in controls.items():
                if control_name in default_controls:
                    if isinstance(control_config, bool):
                        # Enable/disable default control
                        if control_config:
                            final_controls[control_name] = default_controls[
                                control_name
                            ]
                    elif isinstance(control_config, Control):
                        # Replace with custom control
                        final_controls[control_name] = control_config
                    else:
                        raise ValueError(
                            f"Control config for '{control_name}' must be bool or Control, got {type(control_config)}"
                        )
                else:
                    raise ValueError(f"Unknown control name: '{control_name}'")
        elif controls is False:
            # No controls - use values from kwargs
            final_controls = {}
        else:
            raise ValueError(
                f"controls parameter must be bool or dict, got {type(controls)}"
            )

        return final_controls

    @abstractmethod
    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params based on available controls.

        :hierarchy: [Presets | Base | BasePreset | PlotParams]
        :relates-to:
         - motivated_by: "Subclass must define how to build plot parameters"
         - implements: "abstract method: '_build_plot_params'"

        :contract:
         - pre: "final_controls is processed control config, kwargs contains fallback values"
         - post: "Returns plot_params dict for TypedChartBlock"

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        pass

    @abstractmethod
    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs based on available controls.

        :hierarchy: [Presets | Base | BasePreset | PlotKwargs]
        :relates-to:
         - motivated_by: "Subclass must define how to build plot kwargs"
         - implements: "abstract method: '_build_plot_kwargs'"

        :contract:
         - pre: "final_controls is processed control config, kwargs contains fallback values"
         - post: "Returns plot_kwargs dict for TypedChartBlock"

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        pass

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title based on available controls.

        :hierarchy: [Presets | Base | BasePreset | PlotTitle]
        :relates-to:
         - motivated_by: "Optional dynamic title generation"
         - implements: "method: '_get_plot_title'"

        :contract:
         - pre: "final_controls is processed control config"
         - post: "Returns title string with placeholders or None"

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        # Default implementation - subclasses can override
        return None
