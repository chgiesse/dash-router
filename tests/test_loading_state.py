import pytest
from dash_router.core.loading_state import LoadingState, LoadingStates
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
def sample_loading_state_dict():
    return {
        "test": {"state": "done", "node_id": "test_id"},
        "other": {"state": "lacy", "node_id": "other_id"}
    }


def test_loading_state_creation():
    state = LoadingState(state="done", node_id="test_id")
    assert state.state == "done"
    assert state.node_id == "test_id"


def test_loading_state_update():
    state = LoadingState(state="done", node_id="test_id")
    state.update_state("lacy")
    assert state.state == "lacy"


def test_loading_states_creation(sample_loading_state_dict):
    states = LoadingStates(sample_loading_state_dict)
    assert len(states._states) == 2
    assert states._states["test"].state == "done"
    assert states._states["other"].state == "lacy"


def test_loading_states_get_state(sample_loading_state_dict, sample_page_node):
    states = LoadingStates(sample_loading_state_dict)
    assert states.get_state(sample_page_node, "test") == "done"
    assert states.get_state(sample_page_node, "nonexistent") is None


def test_loading_states_set_state(sample_page_node):
    states = LoadingStates({})
    states.set_state(sample_page_node, "test", "done")
    assert states.get_state(sample_page_node, "test") == "done"
    assert states._states["test"].node_id == sample_page_node.node_id


def test_loading_states_get_node_id(sample_loading_state_dict):
    states = LoadingStates(sample_loading_state_dict)
    assert states.get_node_id("test") == "test_id"
    assert states.get_node_id("nonexistent") is None


def test_loading_states_get_all_nodes(sample_loading_state_dict):
    states = LoadingStates(sample_loading_state_dict)
    nodes = states.get_all_nodes()
    assert nodes == {
        "test": "test_id",
        "other": "other_id"
    }


def test_loading_states_to_dict(sample_loading_state_dict):
    states = LoadingStates(sample_loading_state_dict)
    state_dict = states.to_dict()
    assert state_dict == sample_loading_state_dict 