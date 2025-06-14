import pytest
from dash_router.core.execution import ExecNode
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
def sample_exec_node(sample_page_node):
    return ExecNode(
        segment="test",
        node_id=sample_page_node.node_id,
        parent_id="parent_id",
        layout=sample_page_node.layout,
        variables={"var1": "value1"},
    )


@pytest.fixture
def sample_endpoint_results():
    return {
        "test_id": {"data": "test_data"}
    }


async def test_exec_node_creation(sample_page_node):
    exec_node = ExecNode(
        segment="test",
        node_id=sample_page_node.node_id,
        parent_id="parent_id",
        layout=sample_page_node.layout,
        variables={"var1": "value1"},
    )
    
    assert exec_node.segment == "test"
    assert exec_node.node_id == sample_page_node.node_id
    assert exec_node.parent_id == "parent_id"
    assert exec_node.variables == {"var1": "value1"}


async def test_exec_node_execute(sample_exec_node, sample_endpoint_results):
    result = await sample_exec_node.execute(sample_endpoint_results)
    assert isinstance(result, html.Div)
    assert result.children == "Test"


async def test_exec_node_lazy_loading():
    loading_layout = html.Div("Loading...")
    exec_node = ExecNode(
        segment="test",
        node_id="test_id",
        parent_id="parent_id",
        layout=lambda: html.Div("Test"),
        loading=loading_layout,
        is_lacy=True,
        variables={},
    )
    
    result = await exec_node.execute({})
    assert isinstance(result, html.Div)
    assert result.children == "Loading..."


async def test_exec_node_error_handling():
    def error_layout(error, **kwargs):
        return html.Div(f"Error: {str(error)}")
    
    exec_node = ExecNode(
        segment="test",
        node_id="test_id",
        parent_id="parent_id",
        layout=lambda: 1/0,  # This will raise an error
        error=error_layout,
        variables={},
    )
    
    result = await exec_node.execute({})
    assert isinstance(result, html.Div)
    assert "Error: division by zero" in result.children


async def test_exec_node_with_slots():
    slot_layout = html.Div("Slot Content")
    exec_node = ExecNode(
        segment="test",
        node_id="test_id",
        parent_id="parent_id",
        layout=lambda: html.Div("Test"),
        variables={},
        slots={
            "slot1": ExecNode(
                segment="slot1",
                node_id="slot_id",
                parent_id="test_id",
                layout=lambda: slot_layout,
                variables={},
            )
        }
    )
    
    result = await exec_node.execute({})
    assert isinstance(result, html.Div)
    assert result.children == "Test"


async def test_exec_node_with_child():
    child_layout = html.Div("Child Content")
    exec_node = ExecNode(
        segment="test",
        node_id="test_id",
        parent_id="parent_id",
        layout=lambda: html.Div("Test"),
        variables={},
        child_node={
            "children": ExecNode(
                segment="child",
                node_id="child_id",
                parent_id="test_id",
                layout=lambda: child_layout,
                variables={},
            )
        }
    )
    
    result = await exec_node.execute({})
    assert isinstance(result, html.Div)
    assert result.children == "Test" 