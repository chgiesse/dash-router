from .core.routing import PageNode
from .utils.constants import REST_TOKEN


class RouteTreeValidationError(Exception):
    pass


class RouteConfigConflictError(Exception):
    pass


class RouteModuleImportError(Exception):
    pass


class RouteLayoutMissingError(Exception):
    pass


def validate_static_route(node: PageNode):
    if not node.is_static:
        return

    if node.child_nodes:
        raise RouteTreeValidationError(
            f"""
            Route node: {node.module} is marked as static but contains child nodes.
            Either remove the static setting or the child nodes.
            """
        )

    if node.slots:
        raise RouteTreeValidationError(
            f"""
            Route node: {node.module} is marked as static but contains slots.
            Either remove the static setting or the slots.
            """
        )


def validate_default_child(node: PageNode):
    if not node.default_child:
        return

    if node.default_child not in node.child_nodes:
        raise RouteTreeValidationError(
            f"""
            Route node: {node.module} has no child node with name {node.default_child}.
            Default childs have to be present as children.
            """
        )

    if node.default_child and not node.child_nodes:
        raise RouteTreeValidationError(
            f"""
            Route node: {node.module} has no child node.
            Setting default child {node.default_child} is not needed.
            """
        )


def validate_slots(node: PageNode, route_table: dict[str, PageNode]):
    path_templates = []

    for _, slot_id in node.slots.items():
        slot_node = route_table.get(slot_id)
        path_templates.append(slot_node.path_template if slot_node else None)

    # Pass if all pathtemplates are None
    if all([path_template is None for path_template in path_templates]):
        return

    # Pass if every slot has a pathtemplate
    if all([path_template is not None for path_template in path_templates]):
        return

    if (
        len(
            [
                path_template if path_template else None
                for path_template in path_templates
            ]
        )
        == 1
    ):
        return

    raise RouteTreeValidationError(
        f"""
        Slot Validation Error in node {node.module}.
        Either all, none or one slot can be dynamic.
        """
    )


def validate_path_template_children(node: PageNode):
    if not node.path_template:
        return

    if node.child_nodes:
        raise RouteTreeValidationError(
            f"""
            Route node: {node.module} defines a path template and child routes.
            A path template cannot coexist with other child routes at the same level.
            """
        )


def validate_slot_children(node: PageNode):
    if not node.is_slot:
        return

    if node.child_nodes or node.path_template:
        raise RouteTreeValidationError(
            f"""
            Slot node: {node.module} cannot define child routes or path templates.
            Use nested slots instead of route children under a slot.
            """
        )


def validate_catch_all_leaf(node: PageNode):
    if not node.is_path_template or node.segment != REST_TOKEN:
        return

    if node.child_nodes or node.path_template:
        raise RouteTreeValidationError(
            f"""
            Catch-all node: {node.module} must be a leaf route.
            Remove child routes or path templates under the catch-all.
            """
        )


def validate_node(node: PageNode, route_table: dict[str, PageNode]) -> None:
    validate_static_route(node)
    validate_default_child(node)
    validate_slots(node, route_table)
    validate_path_template_children(node)
    validate_slot_children(node)
    validate_catch_all_leaf(node)


def validate_tree(route_table: dict[str, PageNode]) -> None:
    for node in route_table.values():
        validate_node(node, route_table)
