from ast import arg
import importlib
import importlib.util
import json
import os
import traceback
import sys
from typing import Any, Callable, Dict, List, Literal
from uuid import UUID, uuid4
from pathlib import Path

from dash import html, dcc, Input, Output, State, MATCH, callback
from dash._get_paths import app_strip_relative_path
from dash._utils import inputs_to_vals
from dash._validate import validate_and_group_input_args
from dash.development.base_component import Component
from dash_router.core.context import RoutingContext
from dash import Dash
from dash._pages import _parse_query_string, _infer_module_name
from flask import request

from .utils.constants import DEFAULT_LAYOUT_TOKEN
from .utils.helper_functions import (
    format_relative_path,
    path_to_module,
    recursive_to_plotly_json,
    format_relative_path,
    _invoke_layout,
)
from .components import ChildContainer, LacyContainer, RootContainer, SlotContainer
from .core.routing import PageNode, RouteConfig, RouteTable, RouteTree, RouterResponse
from .core.execution import ExecNode
from .core.query_params import extract_function_inputs


class Router:
    def __init__(
        self,
        app: Dash,
        pages_folder: str = "pages",
        requests_pathname_prefix: str | None = None,
        ignore_empty_folders: bool = False,
    ) -> None:
        self.app = app
        self.static_routes = {}
        self.dynamic_routes = {}
        self.route_table = {}
        self.requests_pathname_prefix = requests_pathname_prefix
        self.ignore_empty_folders = ignore_empty_folders
        self.pages_folder = app.pages_folder if hasattr(app, 'pages_folder') and app.pages_folder else pages_folder

        if not isinstance(self.app, Dash):
            raise TypeError(f"App needs to be of Dash not: {type(self.app)}")

        self.setup_route_tree()
        self.setup_router()
        self.setup_lacy_callback()

    def setup_route_tree(self) -> None:
        """Sets up the route tree by traversing the pages folder."""
        # root_dir = ".".join(self.app.server.name.split(os.sep)[:-1])

        pages_path = Path(self.app.config.pages_folder)
        app_dir = pages_path.parent

        if not pages_path.exists():
            raise FileNotFoundError(
                f"Pages folder not found at: {pages_path}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Current working directory: {self.pages_folder}\n"
            )

        self._traverse_directory(str(app_dir), self.pages_folder, None)

    def _validate_node(self, node: PageNode):
        # Validate Slots

        # Validate children
        if node.default_child:
            pass

    def _validate_tree(self):
        for root_node in self.dynamic_routes.routes.items():
            self._validate_node(root_node)

    def _traverse_directory(
        self,
        parent_dir: str,
        segment: str,
        current_node: PageNode | None,
    ) -> None:
        """Recursively traverses the directory structure and registers routes."""
        current_dir = os.path.join(parent_dir, segment)
        if not os.path.exists(current_dir):
            return

        entries = os.listdir(current_dir)
        dir_has_page = "page.py" in entries

        if dir_has_page:
            new_node = self.load_route_module(current_dir, segment, current_node)
            if new_node is not None:

                RouteTable.add_node(new_node)
                RouteTree.add_node(new_node, current_node)

                next_node = new_node
            else:
                next_node = current_node
        else:
            next_node = current_node

        for entry in sorted(entries):
            if entry.startswith((".", "_")) or entry == "page.py":
                continue

            full_path = os.path.join(current_dir, entry)
            if os.path.isdir(full_path):
                self._traverse_directory(current_dir, entry, next_node)

    def load_route_module(
        self, current_dir: str, segment: str, parent_node: PageNode
    ) -> PageNode | None:
        """Load modules and create Page Node"""
        relative_path = os.path.relpath(current_dir, self.app.config.pages_folder)
        relative_path = format_relative_path(relative_path)
        page_module_name = path_to_module(relative_path, "page.py")
        parent_node_id = parent_node.node_id if parent_node else None

        route_config = (
            self.import_route_component(current_dir, "page.py", "config")
            or RouteConfig()
        )
        is_static = route_config.is_static or relative_path == "/"
        is_root = parent_node and parent_node.segment == "/"
        segment = relative_path if is_static else segment

        page_layout = self.import_route_component(current_dir, "page.py")
        loading_layout = self.import_route_component(current_dir, "loading.py")
        error_layout = (
            self.import_route_component(current_dir, "error.py") or self.app._on_error
        )

        endpoint = self.import_route_component(current_dir, "api.py", "endpoint")
        endpoint_inputs, end_types = extract_function_inputs(endpoint)
        layout_inputs, inp_types = extract_function_inputs(page_layout)
        inputs = set(endpoint_inputs + layout_inputs)

        node_id = relative_path # format(abs(hash(relative_path)))
        new_node = PageNode(
            _segment=segment,
            node_id=node_id,
            layout=page_layout,
            parent_id=parent_node_id,
            module=page_module_name,
            is_root=is_root,
            error=error_layout,
            loading=loading_layout,
            endpoint=endpoint,
            endpoint_inputs=inputs,
            path=relative_path,
            is_static=is_static,
            default_child=route_config.default_child,
        )

        return new_node

    def strip_relative_path(self, path: str) -> str:
        return app_strip_relative_path(self.app.config.requests_pathname_prefix, path)

    def import_route_component(
        self,
        current_dir: str,
        file_name: Literal["page.py", "error.py", "loading.py", "api.py"],
        component_name: Literal["layout", "config", "endpoint"] = "layout",
    ) -> Callable[..., Component] | Component | None:
        # page_module_name = path_to_module(current_dir, file_name)
        page_path = os.path.join(current_dir, file_name)
        page_module_name = _infer_module_name(page_path)

        try:
            spec = importlib.util.spec_from_file_location(page_module_name, page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            layout = getattr(module, component_name, None)

            if page_module_name not in sys.modules:
                sys.modules[page_module_name] = module            
       

            if file_name == "page.py" and not layout and component_name == "layout":
                raise ImportError(
                    f"Module {page_module_name} needs a layout function or component"
                )
            return layout

        except ImportError as e:
            if file_name == "page.py" and component_name == "layout":
                print(f"Error processing {page_module_name}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                raise ImportError(
                    f"Module {page_module_name} needs a layout function or component"
                )
        except Exception as e:
            print(f"Error processing {page_module_name}: {e}")
            print(f"Traceback: {traceback.format_exc()}")

        return None

    def build_execution_tree(
        self,
        current_node: PageNode,
        ctx: RoutingContext,
    ) -> ExecNode:
        """
        Recursively builds the execution tree for the matched route.
        It extracts any path variables, processes child nodes, and handles slot nodes.
        """

        if not current_node:
            return current_node

        next_segment = ctx.peek_segment()
        segment_key = current_node.create_segment_key(next_segment)
        print("next_segment", current_node.segment_value, next_segment, segment_key, flush=True)
        is_lacy = ctx.should_lazy_load(current_node, segment_key)

        if current_node.is_path_template:
            ctx.consume_path_var(current_node)
            next_segment = ctx.peek_segment()
        
        print("Current node: ", current_node.child_nodes, current_node.segment_value, current_node.path, flush=True)

        exec_node = ExecNode(
            segment=segment_key,
            node_id=current_node.node_id,
            layout=current_node.layout,
            parent_id=current_node.parent_id,
            variables=ctx.variables,
            loading=current_node.loading,
            error=current_node.error,
            is_lacy=is_lacy,
        )

        if is_lacy:
            ctx.set_node_state(current_node, "done", segment_key)
            return exec_node

        if current_node.endpoint and not DEFAULT_LAYOUT_TOKEN in segment_key:
            ctx.add_endpoint(current_node)

        if current_node.child_nodes or current_node.path_template:
            child_node = current_node.get_child_node(next_segment)

            if not child_node or not child_node.is_path_template:
                ctx.pop_segment()

            child_exec = self.build_execution_tree(
                current_node=child_node,
                ctx=ctx,
            )

            exec_node.child_node = child_exec

        if current_node.slots:
            exec_node.slots = self._process_slot_nodes(
                current_node=current_node,
                ctx=ctx,
            )

        ctx.set_node_state(current_node, "done", segment_key)
        return exec_node

    def _process_slot_nodes(
        self,
        current_node: PageNode,
        ctx: RoutingContext,
    ) -> Dict[str, ExecNode]:
        """Processes all slot nodes defined on the current node."""
        slot_exec_nodes: Dict[str, ExecNode] = {}
        for slot_name, slot_id in current_node.slots.items():
            slot_node = RouteTable.get_node(slot_id)
            segment_key = slot_node.create_segment_key(None)
            ctx.set_node_state(slot_node, "done", segment_key)

            slot_exec_node = self.build_execution_tree(
                current_node=slot_node,
                ctx=ctx,
            )

            slot_exec_nodes[slot_name] = slot_exec_node

        return slot_exec_nodes

    # ─── RESPONSE BUILDER ─────────────────────────────────────
    def resolve_url(
        self,
        pathname: str,
        query_parameters: Dict[str, Any],
        loading_state: Dict[str, Any],
    ) -> RouterResponse:

        path = self.strip_relative_path(pathname)
        ctx = RoutingContext.from_request(
            pathname=path,
            query_params=query_parameters,
            loading_state_dict=loading_state,
            resolve_type="url",
        )

        static_route, path_variables = RouteTree.get_static_route(ctx)
        if static_route:
            layout = _invoke_layout(
                static_route.layout, **query_parameters, **path_variables
            )
            return self.build_response(
                node=static_route, layout=layout, loading_state={}
            )

        active_node = RouteTree.get_active_root_node(ctx, self.ignore_empty_folders)

        if not active_node:
            return self.build_response(node=None, loading_state={})

        exec_tree = self.build_execution_tree(
            current_node=active_node,
            ctx=ctx,
        )

        if not exec_tree:
            return self.build_response(node=None, loading_state={})

        result_data = ctx.gather_endpoints()
        final_layout = exec_tree.execute(result_data)

        new_loading_state = {
            **ctx.get_updated_loading_state(),
            "query_params": query_parameters,
        }

        response = self.build_response(
            node=active_node, loading_state=new_loading_state, layout=final_layout
        )

        return response

    def resolve_search(
        self,
        pathname: str,
        query_params: Dict[str, any],
        updated_query_parameters: Dict[str, any],
        loading_state: Dict[str, any],
    ) -> RouterResponse:

        path = self.strip_relative_path(pathname)
        ctx = RoutingContext.from_request(
            pathname=path,
            loading_state_dict=loading_state,
            query_params=query_params,
            resolve_type="search",
        )

        # Collect all eligible nodes (nodes whose endpoint inputs match updated query parameters)
        eligible_nodes = []
        for _, loaded_node in ctx._loading_states.items():
            node_id = loaded_node.node_id
            node = RouteTable.get_node(node_id)
            if any(
                node_input in updated_query_parameters
                for node_input in node.endpoint_inputs
            ):
                eligible_nodes.append(node)

        if not eligible_nodes:
            return

        # Find parent nodes and create a set of nodes to process
        nodes_to_process_ids = set()
        for node in eligible_nodes:
            current = node
            while current:
                # If we find a parent that needs to be processed, add it and stop traversing
                if any(
                    parent_input in updated_query_parameters
                    for parent_input in current.endpoint_inputs
                ):
                    nodes_to_process_ids.add(current.node_id)
                    break
                current = (
                    RouteTable.get_node(current.parent_id)
                    if current.parent_id
                    else None
                )

        # If no parent nodes need processing, process the eligible nodes directly
        if not nodes_to_process_ids:
            nodes_to_process_ids = {node.node_id for node in eligible_nodes}

        # Build execution trees for all selected nodes
        exec_trees = []
        nodes_to_process = []
        for node_id in nodes_to_process_ids:
            node = RouteTable.get_node(node_id)
            exec_tree = self.build_execution_tree(
                current_node=node,
                ctx=ctx,
            )
            if exec_tree:
                exec_trees.append(exec_tree)
                nodes_to_process.append(node)

        # Gather all endpoints once
        endpoint_results = ctx.gather_endpoints()

        # Execute all trees with the same endpoint results
        layouts = []
        nodes = []
        for exec_tree, node in zip(exec_trees, nodes_to_process):
            layout = exec_tree.execute(endpoint_results)
            if layout:
                layouts.append(layout)
                nodes.append(node)

        new_loading_state = {
            **loading_state,
            **ctx.get_updated_loading_state(),
            "query_params": query_params,
        }

        return self.build_multi_response(nodes, new_loading_state, layouts)

    def build_response(
        self,
        node: PageNode,
        loading_state,
        layout: Component = None,
        remove_layout: bool = False,
    ):
        match node:
            case None:
                container_id = RootContainer.ids.container
                layout = html.H1("404 - Page not found")
                loading_state = {}

            case _ if node.is_root or node.is_static:
                container_id = (
                    RootContainer.ids.container
                    if not remove_layout
                    else json.dumps(ChildContainer.ids.container(node.node_id))
                )

            case _ if node.is_slot:
                container_id = json.dumps(
                    SlotContainer.ids.container(node.parent_id, node.segment)
                )

            case _:
                container_id = json.dumps(
                    ChildContainer.ids.container(
                        node.parent_id if not remove_layout else node.node_id
                    )
                )

        rendered_layout = recursive_to_plotly_json(layout)
        response = {
            container_id: {"children": rendered_layout},
            RootContainer.ids.state_store: {"data": loading_state},
        }
        return RouterResponse(multi=True, response=response)

    def build_multi_response(
        self, nodes: List[PageNode], loading_state, layouts: List[Component]
    ) -> RouterResponse:
        """Builds a response containing multiple layout updates with a single state store."""
        if not nodes or not layouts:
            return self.build_response(None, {})

        response = {}

        for node, layout in zip(nodes, layouts):
            single_response = self.build_response(node, loading_state, layout)
            response.update(single_response.response)

        return RouterResponse(multi=True, response=response)

    # ─── SYNCHRONOUS ROUTER SETUP ───────────────────────────────────────────────────
    def setup_router(self) -> None:
        @self.app.server.before_request
        def router():
            request_data = request.get_data()
            if not request_data:
                return

            body = json.loads(request_data)
            changed_prop = body.get("changedPropIds")

            if changed_prop:
                parts = changed_prop[0].split(".")
                changed_prop_id = parts[0]
                prop = parts[1] if len(parts) > 1 else None
            else:
                return

            if changed_prop_id != RootContainer.ids.location:
                return

            output = body["output"]
            inputs = body.get("inputs", [])
            state = body.get("state", [])
            cb_data = self.app.callback_map[output]
            inputs_state_indices = cb_data["inputs_state_indices"]
            print("inputs_state_indices: ", inputs_state_indices, flush=True)
            args = inputs_to_vals(inputs + state)
            print("ARGS: ", args, flush=True)
            pathname_, search_, loading_state_, states_ = args
            query_parameters = _parse_query_string(search_)
            previous_qp = loading_state_.pop("query_params", {})
            _, func_kwargs = validate_and_group_input_args(args, inputs_state_indices)
            func_kwargs = dict(list(func_kwargs.items())[3:])
            varibales = {**query_parameters, **func_kwargs}

            if prop == "pathname":
                try:
                    response = self.resolve_url(
                        pathname_, varibales, loading_state_
                    )
                    return response.model_dump()
                except Exception:
                    print(f"Traceback: {traceback.format_exc()}")
                    raise Exception("Failed to resolve the URL")

            if prop == "search":
                updated = dict(set(query_parameters.items()) - set(previous_qp.items()))
                missing_keys = previous_qp.keys() - query_parameters.keys()
                missing = {
                    key: None
                    for key in missing_keys
                    if key not in self.app.routing_callback_inputs
                }
                updates = dict(updated.items() | missing.items())
                response = self.resolve_search(
                    pathname_, varibales, updates, loading_state_
                )
                return response.model_dump() if response else response

        with self.app.server.app_context():
            inputs = dict(
                pathname_=Input(RootContainer.ids.location, "pathname"),
                search_=Input(RootContainer.ids.location, "search"),
                loading_state_=State(RootContainer.ids.state_store, "data"),
            )
            inputs.update(self.app.routing_callback_inputs)

            @self.app.callback(
                Output(RootContainer.ids.dummy, "children"),
                inputs=inputs,
            )
            def update(
                pathname_: str, search_: str, loading_state_: str, **states
            ):
                pass

    def setup_lacy_callback(self):
        inputs = dict(
            lacy_segment_id=Input(LacyContainer.ids.container(MATCH), "id"),
            variables=Input(LacyContainer.ids.container(MATCH), "data-path"),
            pathname=State(RootContainer.ids.location, "pathname"),
            search=State(RootContainer.ids.location, "search"),
            loading_state=State(RootContainer.ids.state_store, "data"),
        )

        @self.app.callback(
            Output(LacyContainer.ids.container(MATCH), "children"), inputs=inputs
        )
        def load_lacy_component(
            lacy_segment_id, variables, pathname, search, loading_state
        ):
            print(f"Loading lacy component: {lacy_segment_id}", flush=True)
            print(f"Pathname: {pathname}", flush=True)
            print(f"Search: {search}", flush=True)
            print(f"Loading state: {loading_state}", flush=True)
            print(f"Variables: {variables}", flush=True)
            
            node_id = lacy_segment_id.get("index")
            qs = _parse_query_string(search)
            query_parameters = loading_state.pop("query_params", {})
            node_variables = json.loads(variables)
            variables = {**qs, **query_parameters, **node_variables}
            lacy_node = RouteTable.get_node(node_id)
            path = self.strip_relative_path(pathname)
            segments = path.split("/")
            node_segments = lacy_node.module.split(".")[:-1]
            current_index = node_segments.index(lacy_node.segment_value.replace("_", "-"))
            remaining_segments = list(reversed(segments[current_index:]))

            ctx = RoutingContext.from_request(
                pathname=pathname,
                query_params=variables,
                loading_state_dict=loading_state,
                resolve_type="lacy",
            )

            ctx.segments = remaining_segments

            exec_tree = self.build_execution_tree(
                current_node=lacy_node,
                ctx=ctx,
            )

            endpoint_results = ctx.gather_endpoints()
            layout = exec_tree.execute(endpoint_results)

            return layout
