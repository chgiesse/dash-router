from functools import partial
import importlib
import json
import os
import traceback
from typing import Any, Awaitable, Callable, Dict, List, Literal, Tuple
from uuid import UUID, uuid4

from dash import html
from dash._get_paths import app_strip_relative_path
from dash._utils import inputs_to_vals
from dash._validate import validate_and_group_input_args
from dash.development.base_component import Component
from flash import Flash, Input, Output, State, MATCH, set_props
from flash._pages import _parse_query_string
from quart import request
import asyncio

from .utils.constants import REST_TOKEN, DEFAULT_LAYOUT_TOKEN
from .utils.helper_functions import (
    format_relative_path,
    path_to_module,
    recursive_to_plotly_json,
    create_segment_key,
    extract_function_inputs,
    format_relative_path,
    _invoke_layout,
)
from .components import ChildContainer, LacyContainer, RootContainer, SlotContainer
from .models import RouterResponse, LoadingStateType
from .core.routing import PageNode, RouteConfig, RouteTable, RouteTree
from .core.execution import ExecNode


class Router:
    def __init__(
        self,
        app: Flash,
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
        self.pages_folder = app.pages_folder if app.pages_folder else pages_folder

        if not isinstance(self.app, Flash):
            raise TypeError(f"App needs to be of Flash not: {type(self.app)}")

        self.setup_route_tree()
        self.setup_router()
        self.setup_lacy_callback()

    def setup_route_tree(self) -> None:
        """Sets up the route tree by traversing the pages folder."""
        root_dir = ".".join(self.app.server.name.split(os.sep)[:-1])
        self._traverse_directory(root_dir, self.pages_folder, None)

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
        relative_path = os.path.relpath(current_dir, self.pages_folder)
        relative_path = format_relative_path(relative_path)
        page_module_name = path_to_module(current_dir, "page.py")
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
        endpoint_inputs = extract_function_inputs(endpoint) if endpoint else []

        node_id = str(uuid4())
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
            endpoint_inputs=endpoint_inputs,
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
        page_module_name = path_to_module(current_dir, file_name)
        try:
            page_module = importlib.import_module(page_module_name)
            layout = getattr(page_module, component_name, None)
            if file_name == "page.py" and not layout:
                raise ImportError(
                    f"Module {page_module_name} needs a layout function or component"
                )
            return layout

        except ImportError as e:
            if file_name == "layout.py":
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
        segments: List[str],
        parent_variables: Dict[str, str],
        query_params: Dict[str, Any],
        loading_state: LoadingStateType,
        request_pathname: str,
        endpoints: Dict[UUID, Callable[..., Awaitable[any]]],
        is_init: bool,
    ) -> Tuple[ExecNode, Dict[UUID, Callable[..., Awaitable[any]]]]:
        """
        Recursively builds the execution tree for the matched route.
        It extracts any path variables, processes child nodes, and handles slot nodes.
        """

        if not current_node:
            return current_node, endpoints

        current_variables = {**parent_variables, **query_params}
        next_segment = segments[-1] if segments else None
        segment_key = current_node.create_segment_key(next_segment)
        is_default = DEFAULT_LAYOUT_TOKEN in segment_key
        current_loading_state = loading_state.get(segment_key)
        is_lacy = (
            current_loading_state != "lacy"
            and current_node.loading is not None
            and not is_default
            and is_init
        )

        exec_node = ExecNode(
            segment=segment_key,
            node_id=current_node.node_id,
            layout=current_node.layout,
            parent_id=current_node.parent_id,
            variables=current_variables,
            loading=current_node.loading,
            error=current_node.error,
            is_lacy=is_lacy,
        )

        if current_node.is_path_template:
            varname = current_node.segment
            if current_node.segment == REST_TOKEN:
                varname = "rest"
                next_segment = segments
                segments = []

            current_variables[varname] = next_segment
            segments = segments[:-1]
            exec_node.variables = current_variables
            next_segment = segments[-1] if segments else None

        if is_lacy:
            loading_state[segment_key] = "lacy"
            return exec_node, endpoints

        if current_node.endpoint and not is_default:
            partial_endpoint = partial(current_node.endpoint, **current_variables)
            endpoints[current_node.node_id] = partial_endpoint

        if current_node.child_nodes or current_node.path_template:
            child_node = current_node.get_child_node(next_segment)
            segments = (
                segments[:-1]
                if not child_node or not child_node.is_path_template
                else segments
            )

            child_exec, _ = self.build_execution_tree(
                current_node=child_node,
                segments=segments.copy(),
                parent_variables=current_variables,
                query_params=query_params,
                loading_state=loading_state,
                request_pathname=request_pathname,
                endpoints=endpoints,
                is_init=is_init,
            )

            exec_node.child_node["children"] = child_exec

        if current_node.slots:
            exec_node.slots = self._process_slot_nodes(
                current_node=current_node,
                segments=segments.copy(),
                current_variables=current_variables,
                query_params=query_params,
                loading_state=loading_state,
                requests_pathname=request_pathname,
                endpoints=endpoints,
                is_init=is_init,
            )

        loading_state[segment_key] = "done"
        return exec_node, endpoints

    def _process_slot_nodes(
        self,
        current_node: PageNode,
        segments: List[str],
        current_variables: Dict[str, str],
        query_params: Dict[str, Any],
        loading_state: LoadingStateType,
        requests_pathname: str,
        endpoints: Dict[UUID, Callable[..., Awaitable[any]]],
        is_init: bool = True,
    ) -> Dict[str, ExecNode]:
        """Processes all slot nodes defined on the current node."""
        slot_exec_nodes: Dict[str, ExecNode] = {}
        for slot_name, slot_id in current_node.slots.items():
            slot_node = RouteTable.get_node(slot_id)

            segment_key = create_segment_key(slot_node, current_variables)
            loading_state[segment_key] = "done"

            slot_exec_node, _ = self.build_execution_tree(
                current_node=slot_node,
                segments=segments.copy(),
                parent_variables=current_variables,
                query_params=query_params,
                loading_state=loading_state,
                request_pathname=requests_pathname,
                endpoints=endpoints,
                is_init=is_init,
            )

            slot_exec_nodes[slot_name] = slot_exec_node

        return slot_exec_nodes

    # ─── RESPONSE BUILDER ─────────────────────────────────────
    async def dispatch(
        self,
        pathname: str,
        query_parameters: Dict[str, any],
        loading_state: LoadingStateType,
        is_init: bool = True,
    ) -> RouterResponse:

        path = self.strip_relative_path(pathname)
        static_route, path_variables = RouteTree.get_static_route(path)
        if static_route:
            layout = await _invoke_layout(
                static_route.layout, **query_parameters, **path_variables
            )
            return self.build_response(
                node=static_route, layout=layout, loading_state={}
            )

        init_segments = [seg for seg in pathname.strip("/").split("/") if seg]
        active_node, remaining_segments, updated_segments, path_vars = (
            RouteTree.get_active_root_node(
                init_segments, loading_state, self.ignore_empty_folders
            )
        )
        if not active_node:
            return self.build_response(node=None, loading_state={})

        exec_tree, endpoints = self.build_execution_tree(
            current_node=active_node,
            segments=remaining_segments,
            parent_variables=path_vars,
            query_params=query_parameters,
            loading_state=updated_segments,
            request_pathname=path,
            is_init=is_init,
            endpoints={},
        )

        if not exec_tree:
            return self.build_response(node=None, loading_state={})

        result_data = await self.gather_endpoints(endpoints)
        final_layout = await exec_tree.execute(result_data, is_init)

        new_loading_state = {**updated_segments, "query_params": query_parameters}

        response = self.build_response(
            node=active_node, loading_state=new_loading_state, layout=final_layout
        )

        return response

    async def resolve_search(
        self,
        pathname: str,
        query_params: Dict[str, any],
        updated_query_parameters: Dict[str, any],
        loading_state: LoadingStateType,
    ) -> RouterResponse:

        path = self.strip_relative_path(pathname)
        init_segments = [seg for seg in pathname.strip("/").split("/") if seg]
        active_node, remaining_segments, updated_segments, path_vars = (
            self._get_root_node(init_segments, {})
        )
        segment_key = create_segment_key(active_node, path_vars)
        active_loading_state = loading_state.get(segment_key)
        print("segment_key", segment_key, flush=True)
        print("active_loading_state", active_loading_state, flush=True)
        print("updated_query_parameters", updated_query_parameters, flush=True)
        print("query_params", query_params, flush=True)
        print("endpoint_inputs", active_node.endpoint_inputs, flush=True)

        if set(active_node.endpoint_inputs.keys()).intersection(
            set(updated_query_parameters.keys())
        ):
            # exec_node = ExecNode(
            #     node_id=current_node.node_id,
            #     layout=current_node.layout,
            #     segment=current_node.segment,
            #     parent_segment=current_node.parent_segment,
            #     variables=current_variables,
            #     loading_state=loading_state,
            #     path_template=current_node.path_template,
            #     loading=current_node.loading,
            #     error=current_node.error,
            #     path=request_pathname,
            # )
            print("Load function", active_node.segment, flush=True)

        for segment in remaining_segments:
            current_node = active_node if not current_node else current_node
            next_node = active_node.get_child_node(segment, self.route_table)

            for slot_name, slot_id in current_node.slots.items():
                slot_node = self.route_table.get(slot_id)
                print(slot_name, flush=True)

        # for segment in remaining_segments:

        # container_id = RootContainer.ids.container
        # if active_node.parent_segment != "/":
        #     if active_node.is_slot:
        #         container_id = json.dumps(
        #             SlotContainer.ids.container(
        #                 active_node.parent_segment, active_node.segment
        #             )
        #         )
        #     else:
        #         container_id = json.dumps(
        #             ChildContainer.ids.container(active_node.parent_segment)
        #         )

        # return self._build_response(
        #     container_id, final_layout, new_loading_state, is_init
        # )

    @staticmethod
    async def gather_endpoints(endpoints: Dict[UUID, Callable[..., Awaitable[any]]]):
        if not endpoints:
            return {}

        keys = list(endpoints.keys())
        funcs = list(endpoints.values())
        results = await asyncio.gather(
            *[func() for func in funcs], return_exceptions=True
        )
        return dict(zip(keys, results))

    def build_response(self, node: PageNode, loading_state, layout: Component = None):
        match node:
            case None:
                container_id = RootContainer.ids.container
                layout = html.H1("404 - Page not found")
                loading_state = {}

            case _ if node.is_root or node.is_static:
                container_id = RootContainer.ids.container

            case _ if node.is_slot:
                container_id = json.dumps(
                    SlotContainer.ids.container(node.parent_id, node.segment)
                )

            case _:
                container_id = json.dumps(ChildContainer.ids.container(node.parent_id))

        rendered_layout = recursive_to_plotly_json(layout)

        response = {
            container_id: {"children": rendered_layout},
            RootContainer.ids.state_store: {"data": loading_state},
        }
        return RouterResponse(multi=True, response=response)

    # ─── ASYNC & SYNC ROUTER SETUP ───────────────────────────────────────────────────
    def setup_router(self) -> None:
        @self.app.server.before_request
        async def router():
            request_data = await request.get_data()
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

            print("--------", flush=True)
            output = body["output"]
            inputs = body.get("inputs", [])
            state = body.get("state", [])
            cb_data = self.app.callback_map[output]
            inputs_state_indices = cb_data["inputs_state_indices"]
            args = inputs_to_vals(inputs + state)
            pathname_, search_, loading_state_, states_ = args
            query_parameters = _parse_query_string(search_)
            previous_qp = loading_state_.pop("query_params", {})
            if prop == "pathname":
                try:
                    # Skip the arguments required for routing
                    _, func_kwargs = validate_and_group_input_args(
                        args, inputs_state_indices
                    )
                    func_kwargs = dict(list(func_kwargs.items())[3:])
                    varibales = {**query_parameters, **func_kwargs}
                    response = await self.dispatch(pathname_, varibales, loading_state_)
                    return response.model_dump()
                except Exception:
                    print(f"Traceback: {traceback.format_exc()}")
                    raise Exception("Failed to resolve the URL")

            if prop == "search":
                updated = dict(set(query_parameters.items()) - set(previous_qp.items()))
                missing_keys = previous_qp.keys() - query_parameters.keys()
                missing = {key: None for key in missing_keys}
                updates = dict(updated.items() | missing.items())
                print("query_parameters", query_parameters, flush=True)
                print("previous_qp", previous_qp, flush=True)
                print("updated", updated, flush=True)
                print("missing_keys", missing_keys, flush=True)
                print("missing", missing, flush=True)
                print("updates", updates, flush=True)
                await self.resolve_search(
                    pathname_, query_parameters, updates, loading_state_
                )

        @self.app.server.before_serving
        async def trigger_router():
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
            async def update(
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
        async def load_lacy_component(
            lacy_segment_id, variables, pathname, search, loading_state
        ):
            node_id = lacy_segment_id.get("index")
            query_parameters = _parse_query_string(search)
            node_variables = json.loads(variables)
            lacy_node = RouteTable.get_node(node_id)
            path = self.strip_relative_path(pathname)
            segments = path.split("/")
            node_segments = lacy_node.module.split(".")[1:-1]
            current_index = node_segments.index(lacy_node.segment_value)
            remaining_segments = list(reversed(segments[current_index:]))

            exec_tree, endpoints = self.build_execution_tree(
                current_node=lacy_node,
                segments=remaining_segments,
                parent_variables=node_variables,
                query_params=query_parameters,
                loading_state=loading_state,
                request_pathname=path,
                endpoints={},
                is_init=False,
            )

            endpoint_results = await self.gather_endpoints(endpoints)
            layout = await exec_tree.execute(
                is_init=False, endpoint_results=endpoint_results
            )
            new_loading_state = {
                key: val if val != "lacy" else "done"
                for key, val in loading_state.items()
            }
            if layout:
                set_props(RootContainer.ids.state_store, {"data": new_loading_state})
            return layout
