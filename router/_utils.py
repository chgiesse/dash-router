def create_pathtemplate_key(
    segment: str, path_template: str, path_variable: str, template_key: str
):
    if path_variable and path_template:
        filled_template = path_template.replace(template_key, path_variable)
        path_template_key = segment + filled_template
        return path_template_key
    return segment
