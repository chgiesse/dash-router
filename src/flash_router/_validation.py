from typing import Dict
from uuid import UUID

from .core.routing import PageNode


class RouteTreeValidationError(Exception):
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


def validate_slots(node: PageNode, route_table: Dict[UUID, PageNode]):
    path_templates = []

    for _, slot_id in node.slots.items():
        slot_node = route_table.get(slot_id)
        path_templates.append(slot_node.path_template)

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


def validate_child_nodes():
    pass


def validate_slot_pathtemplates():
    pass
