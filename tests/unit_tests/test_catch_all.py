from pathlib import Path

from flash_router.core.context import RoutingContext
from flash_router.core.routing import RouteTree

from utils.helpers import done_state, get_leaf_node, get_node_by_path


def test_projects_files_rest_empty(router):
    projects_node = get_node_by_path("projects")
    team_node = get_node_by_path("projects/[team_id]")
    files_node = get_node_by_path("projects/[team_id]/files")
    rest_node = get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            done_state(projects_node, "alpha"),
            done_state(team_node, "alpha"),
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
    leaf_node = get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == []


def test_projects_files_rest_single_segment(router):
    projects_node = get_node_by_path("projects")
    team_node = get_node_by_path("projects/[team_id]")
    files_node = get_node_by_path("projects/[team_id]/files")
    rest_node = get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            done_state(projects_node, "alpha"),
            done_state(team_node, "alpha"),
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
    leaf_node = get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1"]


def test_projects_files_rest_multiple_segments(router):
    projects_node = get_node_by_path("projects")
    team_node = get_node_by_path("projects/[team_id]")
    files_node = get_node_by_path("projects/[team_id]/files")
    rest_node = get_node_by_path("projects/[team_id]/files/[__rest]")

    loading_state = dict(
        [
            done_state(projects_node, "alpha"),
            done_state(team_node, "alpha"),
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
    leaf_node = get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1", "2", "3"]


def test_root_files_rest_multiple_segments(router):
    files_node = get_node_by_path("files")
    rest_node = get_node_by_path("files/[__rest]")

    ctx = RoutingContext.from_request(
        pathname="/files/1/2/3",
        query_params={},
        loading_state_dict={},
        resolve_type="url",
    )

    active_node = RouteTree.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == files_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = get_leaf_node(exec_tree)

    assert leaf_node.node_id == rest_node.node_id
    assert ctx.path_vars["rest"] == ["1", "2", "3"]
