from flash_router.core.routing import RouteRegistry, RoutingContext

from utils.helpers import done_state, get_leaf_node, get_node_by_path


def test_tickets_root_active_node(router):
    tickets_node = get_node_by_path("tickets")
    ticket_node = get_node_by_path("tickets/[ticket_id]")

    ctx = RoutingContext.from_request(
        pathname="/tickets",
        query_params={},
        loading_state_dict={},
        resolve_type="url",
    )

    active_node = RouteRegistry.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == tickets_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    leaf_node = get_leaf_node(exec_tree)

    assert leaf_node.node_id == ticket_node.node_id


def test_tickets_ticket_id_slot_roots(router):
    tickets_node = get_node_by_path("tickets")
    ticket_node = get_node_by_path("tickets/[ticket_id]")
    detail_node = get_node_by_path("tickets/[ticket_id]/(detail)")
    activity_node = get_node_by_path("tickets/[ticket_id]/(activity)")

    loading_state = dict(
        [
            done_state(tickets_node, "1001"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/tickets/1001",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteRegistry.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == ticket_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)

    assert ctx.path_vars["ticket_id"] == "1001"
    assert set(exec_tree.slots.keys()) == {"detail", "activity"}

    detail_leaf = get_leaf_node(exec_tree.slots["detail"])
    activity_leaf = get_leaf_node(exec_tree.slots["activity"])

    assert detail_leaf.node_id == detail_node.node_id
    assert activity_leaf.node_id == activity_node.node_id


def test_tickets_ticket_id_detail_nested_slot(router):
    tickets_node = get_node_by_path("tickets")
    ticket_node = get_node_by_path("tickets/[ticket_id]")
    detail_node = get_node_by_path("tickets/[ticket_id]/(detail)")
    summary_node = get_node_by_path("tickets/[ticket_id]/(detail)/(summary)")

    loading_state = dict(
        [
            done_state(tickets_node, "1001"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/tickets/1001",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteRegistry.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == ticket_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    detail_exec = exec_tree.slots["detail"]

    assert ctx.path_vars["ticket_id"] == "1001"
    assert detail_exec.node_id == detail_node.node_id
    assert detail_exec.slots["summary"].node_id == summary_node.node_id


def test_tickets_ticket_id_activity_nested_slot(router):
    tickets_node = get_node_by_path("tickets")
    ticket_node = get_node_by_path("tickets/[ticket_id]")
    activity_node = get_node_by_path("tickets/[ticket_id]/(activity)")
    comments_node = get_node_by_path("tickets/[ticket_id]/(activity)/(comments)")

    loading_state = dict(
        [
            done_state(tickets_node, "1001"),
        ]
    )
    ctx = RoutingContext.from_request(
        pathname="/tickets/1001",
        query_params={},
        loading_state_dict=loading_state,
        resolve_type="url",
    )

    active_node = RouteRegistry.get_active_root_node(ctx, ignore_empty_folders=False)

    assert active_node.node_id == ticket_node.node_id

    exec_tree = router.build_execution_tree(current_node=active_node, ctx=ctx)
    activity_exec = exec_tree.slots["activity"]

    assert ctx.path_vars["ticket_id"] == "1001"
    assert activity_exec.node_id == activity_node.node_id
    assert activity_exec.slots["comments"].node_id == comments_node.node_id
