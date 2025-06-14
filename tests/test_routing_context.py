import pytest
from dash_router.core.routing_context import RoutingContext
from dash_router.core.routing import PageNode
from dash_router.models import LoadingStateType
from uuid import uuid4


@pytest.fixture
def sample_page_node():
    return PageNode(
        _segment="test",
        node_id=str(uuid4()),
        layout=lambda: None,
        module="test_module",
    )


@pytest.fixture
def sample_loading_state():
    return {
        "test": {"state": "done", "node_id": "test_id"},
        "query_params": {"param1": "value1"}
    }


def test_routing_context_creation():
    context = RoutingContext.from_request(
        pathname="/test/path",
        query_params={"param1": "value1"},
        loading_state_dict={},
        is_init=True
    )
    
    assert context.pathname == "/test/path"
    assert context.query_params == {"param1": "value1"}
    assert context.is_init is True
    assert context._segments == ["test", "path"]


def test_routing_context_with_loading_state(sample_loading_state):
    context = RoutingContext.from_request(
        pathname="/test/path",
        query_params={"param1": "value1"},
        loading_state_dict=sample_loading_state,
        is_init=True
    )
    
    assert "query_params" not in context.loading_states.to_dict()
    assert context.loading_states.get_state(None, "test") == "done"


def test_node_state_management(sample_page_node):
    context = RoutingContext.from_request(
        pathname="/test/path",
        query_params={},
        loading_state_dict={},
        is_init=True
    )
    
    context.set_node_state(sample_page_node, "done")
    assert context.get_node_state(sample_page_node) == "done"


def test_path_variable_consumption(sample_page_node):
    context = RoutingContext.from_request(
        pathname="/test/123",
        query_params={},
        loading_state_dict={},
        is_init=True
    )
    
    sample_page_node.is_path_template = True
    sample_page_node.segment = "id"
    
    value = context.consume_path_var(sample_page_node)
    assert value == "123"
    assert context.path_vars["id"] == "123"


def test_rest_path_variable():
    context = RoutingContext.from_request(
        pathname="/test/123/456/789",
        query_params={},
        loading_state_dict={},
        is_init=True
    )
    
    rest_node = PageNode(
        _segment="[...rest]",
        node_id=str(uuid4()),
        layout=lambda: None,
        module="test_module",
    )
    
    value = context.consume_path_var(rest_node)
    assert value == ["789", "456", "123"]
    assert context.path_vars["rest"] == ["789", "456", "123"]


def test_lazy_loading_check(sample_page_node):
    context = RoutingContext.from_request(
        pathname="/test/path",
        query_params={},
        loading_state_dict={},
        is_init=True
    )
    
    sample_page_node.loading = lambda: None
    assert context.should_lazy_load(sample_page_node) is True
    
    context.set_node_state(sample_page_node, "lacy")
    assert context.should_lazy_load(sample_page_node) is False


def test_to_loading_state_dict():
    context = RoutingContext.from_request(
        pathname="/test/path",
        query_params={"param1": "value1"},
        loading_state_dict={},
        is_init=True
    )
    
    state_dict = context.to_loading_state_dict()
    assert "query_params" in state_dict
    assert state_dict["query_params"] == {"param1": "value1"} 