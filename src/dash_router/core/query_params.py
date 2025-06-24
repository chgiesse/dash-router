from typing import Callable, get_type_hints, get_origin
from pydantic import BaseModel
import inspect


def classify_type(obj):
    """Classify what kind of type this is"""
    if not inspect.isclass(obj) and get_origin(obj) is None:
        return "not_a_type"

    # Handle typing generics
    if hasattr(obj, "__module__"):
        if obj.__module__ == "builtins":
            return "builtin"
        elif obj.__module__ == "typing":
            return "typing"

    # Check if it's a Pydantic model
    if inspect.isclass(obj) and issubclass(obj, BaseModel):
        return "pydantic"

    return "custom_class"


def should_skip(obj):
    """Skip everything except builtins and pydantic models"""
    return classify_type(obj) not in ("builtin", "typing", "pydantic")


def extract_function_inputs(func: Callable):
    """Recursively extracts function & class inputs"""
    valid_classes = ("builtin", "typing", "pydantic")
    inputs = []
    types = {}

    if not func:
        return inputs, types

    for param_name, param_type in get_type_hints(func).items():
        type_class = classify_type(param_type)

        if type_class not in valid_classes:
            continue

        if type_class == "pydantic":
            model_inputs = extract_pydantic_fields(param_type)
            inputs += model_inputs
            types[param_name] = param_type
            continue

        types[param_name] = param_type
        inputs.append(param_name)

    return inputs, types


def extract_pydantic_fields(model_class):
    """Extract fields from a Pydantic model"""
    fields = []
    for field_name, _ in model_class.model_fields.items():
        fields.append(field_name)

    return fields
