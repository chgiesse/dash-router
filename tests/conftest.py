import pytest
from dash_router.core.routing import PageNode
from dash import html
from uuid import uuid4


@pytest.fixture
def sample_page_node():
    return PageNode(
        _segment="test",
        node_id=str(uuid4()),
        layout=lambda: html.Div("Test"),
        module="test_module",
    )


@pytest.fixture
def sample_loading_state_dict():
    return {
        "test": {"state": "done", "node_id": "test_id"},
        "other": {"state": "lacy", "node_id": "other_id"}
    }


@pytest.fixture
def sample_endpoint_results():
    return {
        "test_id": {"data": "test_data"}
    } 