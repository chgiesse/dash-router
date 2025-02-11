import os


def create_pathtemplate_key(
    segment: str, path_template: str, path_variable: str, template_key: str
):
    if path_variable and path_template:
        filled_template = path_template.replace(template_key, path_variable)
        path_template_key = segment + filled_template
        return path_template_key
    return segment


def recursive_to_plotly_json(component):
    if hasattr(component, "to_plotly_json"):
        component = component.to_plotly_json()
        children = component["props"].get("children")

        if isinstance(children, list):
            component["props"]["children"] = [
                recursive_to_plotly_json(child) for child in children
            ]
        else:
            component["props"]["children"] = recursive_to_plotly_json(children)

    return component


def format_segment(segment: str):
    formatted_segment = segment.strip("()").replace("_", "-").replace(" ", "-")

    return formatted_segment


def path_to_module(current_dir: str, module: str):
    module_path = os.path.join(current_dir, module)
    module_path_parts = os.path.splitext(module_path)[0].split(os.sep)
    module_name = ".".join(module_path_parts)
    return module_name
