from asyncio import iscoroutinefunction
from inspect import iscoroutine
from .constants import DEFAULT_LAYOUT_TOKEN

import os
from _plotly_utils.optional_imports import get_module
from plotly.io._json import clean_to_json_compatible, config, JsonConfig
from typing import get_type_hints, get_origin
from pydantic import BaseModel
from fnmatch import fnmatch
import re


async def _invoke_layout(func, *func_args, **func_kwargs):
    if iscoroutinefunction(func):
        return await func(*func_args, **func_kwargs)

    if callable(func):
        return func(*func_args, **func_kwargs)

    return func


def create_pathtemplate_key(
    segment: str, path_template: str, path_variable: str, template_key: str
):
    if path_variable and path_template:
        filled_template = path_template.replace(template_key, path_variable)
        path_template_key = segment + filled_template
        return path_template_key
    return segment


def recursive_to_plotly_json(component):
    """
    Recursively convert a component to a JSON-serializable structure.
    Handles Plotly components, numpy arrays, pandas objects, dates/times, and other special types.

    Parameters:
    -----------
    component: Any
        The component to convert

    Returns:
    --------
    A JSON-serializable representation of the component
    """
    # Base case: simple types don't need conversion
    if component is None or isinstance(component, (str, int, float, bool)):
        return component

    # Try to handle numpy arrays first
    try:
        import numpy as np

        if isinstance(component, np.ndarray):
            return component.tolist()
        elif np.isscalar(component) and not isinstance(
            component, (bool, int, float, complex)
        ):
            return component.item()
    except (ImportError, AttributeError):
        pass

    # Handle pandas objects
    try:
        import pandas as pd

        if isinstance(component, (pd.Series, pd.DataFrame)):
            return component.to_dict()
        elif isinstance(component, pd.Timestamp):
            return component.isoformat()
        elif component is pd.NaT:
            return None
    except (ImportError, AttributeError):
        pass

    # Handle datetime objects
    try:
        import datetime

        if isinstance(component, (datetime.date, datetime.datetime)):
            return component.isoformat()
    except (ImportError, AttributeError):
        pass

    # Handle decimal
    try:
        import decimal

        if isinstance(component, decimal.Decimal):
            return float(component)
    except (ImportError, AttributeError):
        pass

    # Convert component to plotly json if it has the method
    if hasattr(component, "to_plotly_json"):
        component = component.to_plotly_json()

    # Also try other common serialization methods
    if hasattr(component, "tolist"):
        try:
            return component.tolist()
        except Exception:
            pass

    if hasattr(component, "to_dict"):
        try:
            return component.to_dict()
        except Exception:
            pass

    # Make sure component is a dictionary before checking for "props"
    if isinstance(component, dict):
        # Process props
        for key, value in list(component.items()):
            if isinstance(value, list):
                # Process lists of items
                component[key] = [recursive_to_plotly_json(item) for item in value]
            else:
                # Process single items
                component[key] = recursive_to_plotly_json(value)

    # Handle list-type components
    elif isinstance(component, list):
        component = [recursive_to_plotly_json(item) for item in component]

    # As a last resort, try string representation
    else:
        try:
            return str(component)
        except Exception:
            return None

    return component


def format_relative_path(path: str):
    return path.replace(".", "/").replace("_", "-").replace(" ", "-")


def format_segment(segment: str, is_slot: bool = False):
    if is_slot:
        formatted_segment = segment.strip("()")
    else:
        formatted_segment = segment.replace("_", "-").replace(" ", "-")

    return formatted_segment


def path_to_module(current_dir: str, module: str):
    module_path = os.path.join(current_dir, module)
    module_path_parts = os.path.splitext(module_path)[0].split(os.sep)
    module_name = ".".join(module_path_parts)
    return module_name


def to_json_plotly(plotly_object, pretty=False, engine=None):
    """
    Convert a plotly/Dash object to a JSON string representation

    Parameters
    ----------
    plotly_object:
        A plotly/Dash object represented as a dict, graph_object, or Dash component

    pretty: bool (default False)
        True if JSON representation should be pretty-printed, False if
        representation should be as compact as possible.

    engine: str (default None)
        The JSON encoding engine to use. One of:
          - "json" for an engine based on the built-in Python json module
          - "orjson" for a faster engine that requires the orjson package
          - "auto" for the "orjson" engine if available, otherwise "json"
        If not specified, the default engine is set to the current value of
        plotly.io.json.config.default_engine.

    Returns
    -------
    str
        Representation of input object as a JSON string

    See Also
    --------
    to_json : Convert a plotly Figure to JSON with validation
    """
    orjson = get_module("orjson", should_load=True)

    # Determine json engine
    if engine is None:
        engine = config.default_engine

    if engine == "auto":
        if orjson is not None:
            engine = "orjson"
        else:
            engine = "json"
    elif engine not in ["orjson", "json"]:
        raise ValueError("Invalid json engine: %s" % engine)

    modules = {
        "sage_all": get_module("sage.all", should_load=False),
        "np": get_module("numpy", should_load=False),
        "pd": get_module("pandas", should_load=False),
        "image": get_module("PIL.Image", should_load=False),
    }

    # Dump to a JSON string and return
    # --------------------------------
    if engine == "json":
        opts = {}
        if pretty:
            opts["indent"] = 2
        else:
            # Remove all whitespace
            opts["separators"] = (",", ":")

        from _plotly_utils.utils import PlotlyJSONEncoder

        return _plotly_object

    elif engine == "orjson":
        JsonConfig.validate_orjson()
        opts = orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY

        if pretty:
            opts |= orjson.OPT_INDENT_2

        # Plotly
        try:
            plotly_object = plotly_object.to_plotly_json()
        except AttributeError:
            pass

        # Try without cleaning
        try:
            return plotly_object

        except TypeError:
            pass

        cleaned = clean_to_json_compatible(
            plotly_object,
            numpy_allowed=True,
            datetime_allowed=True,
            modules=modules,
        )
        return cleaned


def create_segment_key(page_node, variables):
    segment_key = page_node.segment

    if page_node.is_path_template:
        path_key = page_node.segment
        path_variable = (
            variables.get(path_key) or DEFAULT_LAYOUT_TOKEN
            if page_node.is_slot
            else None
        )
        segment_key = create_pathtemplate_key(
            page_node.segment, page_node.path_template, path_variable, path_key
        )

    return segment_key


def extract_function_inputs(func):
    type_hints = get_type_hints(func)
    inputs = []
    for param_name, type_hint in type_hints.items():
        origin = get_origin(type_hint)
        inputs.append(param_name)
        print(param_name, type_hint, flush=True)
        if not origin and issubclass(type_hint, BaseModel):
            fields = type_hint.model_fields
            inputs += list(fields.keys())
    return set(inputs)


def _parse_path_variables(pathname, path_template):
    """
    creates the dict of path variables passed to the layout
    e.g. path_template= "/asset/<asset_id>"
         if pathname provided by the browser is "/assets/a100"
         returns **{"asset_id": "a100"}
    """

    # parse variable definitions e.g. <var_name> from template
    # and create pattern to match
    wildcard_pattern = re.sub("[.*?]", "*", path_template)
    var_pattern = re.sub("[.*?]", "(.*)", path_template)

    # check that static sections of the pathname match the template
    if not fnmatch(pathname, wildcard_pattern):
        return None

    # parse variable names e.g. var_name from template
    var_names = re.findall("[(.*?)]", path_template)

    # parse variables from path
    variables = re.findall(var_pattern, pathname)
    variables = variables[0] if isinstance(variables[0], tuple) else variables

    return dict(zip(var_names, variables))
