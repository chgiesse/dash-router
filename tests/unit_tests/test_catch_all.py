from pathlib import Path

import pytest
from dash._utils import AttributeDict
from flash import Flash

from flash_router import FlashRouter
from flash_router.core.context import RoutingContext
from flash_router.core.routing import RouteTable, RouteTree
from flash_router.utils.helper_functions import format_relative_path


def _get_leaf_node(exec_node):
    current = exec_node
    while current and current.child_node and current.child_node != "default":
        current = current.child_node
    return current


def _done_state(node, next_segment):
    segment_key = node.create_segment_key(next_segment)
    return segment_key, {"state": "done", "node_id": node.node_id}


def _get_node_by_path(path):
    formatted_path = format_relative_path(path)
    for node in RouteTable._table.values():
        if node.path == formatted_path:
            return node
    return None


@pytest.fixture(autouse=True)
def reset_route_state():
    RouteTable._table = {}
    RouteTree._static_routes = {}
    RouteTree._dynamic_routes = AttributeDict(routes={}, path_template=None)
    yield


@pytest.fixture()
def router():
    pages_dir = Path(__file__).resolve().parents[1] / "pages"
    app = Flash(
        __name__,
        prevent_initial_callbacks=True,
        pages_folder=str(pages_dir),
        use_pages=False,
    )
    return FlashRouter(app)


def test_projects_files_rest_empty(router):
    projects_node = _get_node_by_path("projects")
    team_node = _get_node_by_path("projects/[team_id]")
    files_node = _get_node_by_path("projects/[team_id]/files")
    rest_node = _get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            _done_state(projects_node, "alpha"),
            _done_state(team_node, "alpha"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/projects/alpha/files",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteTree.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == files_node.node_id
    assert ctx.path_vars["team_id"] == "alpha"

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = _get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == []


def test_projects_files_rest_single_segment(router):
    projects_node = _get_node_by_path("projects")
    team_node = _get_node_by_path("projects/[team_id]")
    files_node = _get_node_by_path("projects/[team_id]/files")
    rest_node = _get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            _done_state(projects_node, "alpha"),
            _done_state(team_node, "alpha"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/projects/alpha/files/1",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteTree.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == files_node.node_id
    assert ctx.path_vars["team_id"] == "alpha"

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = _get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1"]


def test_projects_files_rest_multiple_segments(router):
    projects_node = _get_node_by_path("projects")
    team_node = _get_node_by_path("projects/[team_id]")
    files_node = _get_node_by_path("projects/[team_id]/files")
    rest_node = _get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            _done_state(projects_node, "alpha"),
            _done_state(team_node, "alpha"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/projects/alpha/files/1/2/3",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteTree.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == files_node.node_id
    assert ctx.path_vars["team_id"] == "alpha"

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = _get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1", "2", "3"]


def test_root_files_rest_multiple_segments(router):
    files_node = _get_node_by_path("files")
    rest_node = _get_node_by_path("files/[__rest]")

    ctx = RoutingContext.from_request(
        pathname="/files/1/2/3",
        query_params={},
        loading_state_dict={},
        resolve_type="url",
    )

    active_node = RouteTree.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == files_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = _get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1", "2", "3"]
