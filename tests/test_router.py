# import pytest
# from dash_router.core.router import Router
# from dash_router.core.routing import PageNode
# from dash import html
# from uuid import uuid4


# def test_router_initialization():
#     router = Router()
#     assert router._page_nodes == {}
#     assert router._endpoints == {}
#     assert router._loading_state is not None


# def test_register_page():
#     router = Router()
#     node = PageNode(
#         _segment="test",
#         node_id=str(uuid4()),
#         layout=lambda: html.Div("Test"),
#         module="test_module",
#     )
#     router.register_page(node)
#     assert "test" in router._page_nodes
#     assert router._page_nodes["test"] == node


# def test_register_endpoint():
#     router = Router()
#     router.register_endpoint("test_id", lambda: {"data": "test"})
#     assert "test_id" in router._endpoints


# def test_build_execution_tree():
#     router = Router()
#     node = PageNode(
#         _segment="test",
#         node_id=str(uuid4()),
#         layout=lambda: html.Div("Test"),
#         module="test_module",
#     )
#     router.register_page(node)
#     router.register_endpoint(node.node_id, lambda: {"data": "test"})
    
#     tree = router.build_execution_tree("test")
#     assert tree is not None
#     assert tree.node_id == node.node_id
#     assert tree.module == node.module
#     assert tree.layout == node.layout
#     assert tree.endpoint is not None


# def test_build_execution_tree_with_invalid_path():
#     router = Router()
#     tree = router.build_execution_tree("invalid")
#     assert tree is None


# def test_build_execution_tree_without_endpoint():
#     router = Router()
#     node = PageNode(
#         _segment="test",
#         node_id=str(uuid4()),
#         layout=lambda: html.Div("Test"),
#         module="test_module",
#     )
#     router.register_page(node)
    
#     tree = router.build_execution_tree("test")
#     assert tree is not None
#     assert tree.node_id == node.node_id
#     assert tree.module == node.module
#     assert tree.layout == node.layout
#     assert tree.endpoint is None 