# from dataclasses import dataclass
import importlib
import json
import os
import traceback
from typing import Dict, List, Optional, Tuple, Union

from dash import Dash, html
from dash._get_paths import app_strip_relative_path
from dash._utils import inputs_to_vals

# from dash.development.base_component import Component
from flash import Flash, Input, Output, State
from flash._pages import _parse_path_variables, _parse_query_string
from quart import request

from ._utils import create_pathtemplate_key, recursive_to_plotly_json
from .components import ChildContainer, RootContainer, SlotContainer
from .models import ExecNode, PageNode, RootNode, RouteConfig

# from dataclasses import dataclass, field
# import asyncio


class Router:
    def __init__(
        self,
        app: Union[Dash, Flash],
        pages_folder: str = "pages",
        requests_pathname_prefix: str = None,
        ignore_empty_folders: bool = False,
    ) -> None:
        self.app = app
        self.route_registry = RootNode()
        self.static_routes = RootNode()
        self.dynamic_routes = RootNode()
        self.requests_pathname_prefix = requests_pathname_prefix
        self.ignore_empty_folders = ignore_empty_folders
        self.pages_folder = app.pages_folder if app.pages_folder else pages_folder

        if isinstance(self.app, Dash):
            self.is_async = False
        elif isinstance(self.app, Flash):
            self.is_async = True
        else:
            raise TypeError(
                f"App needs to be of type Dash or flash not: {type(self.app)}"
            )

        self.setup_route_tree()

        self.setup_router()

    def setup_route_tree(self) -> None:
        root_dir = ".".join(self.app.server.name.split(os.sep)[:-1])
        self._traverse_directory(root_dir, self.pages_folder, self.route_registry)

    def _traverse_directory(
        self, parent_dir: str, segment: str, current_node: Union[RootNode, PageNode]
    ):
        current_dir = os.path.join(parent_dir, segment)
        if not os.path.exists(current_dir):
            return

        entries = os.listdir(current_dir)
        dir_has_page = "page.py" in entries

        if dir_has_page:
            new_node = self.load_route_module(current_dir, segment, current_node)
            # Set the path based on the directory structure
            if current_dir == self.pages_folder:
                new_node.path = "/"
                new_node.segment = "/"
                new_node.parent_segment = None
                self.route_registry.register_root_route(new_node)

            else:
                # Remove the base directory from the path
                relative_path = os.path.relpath(current_dir, self.pages_folder)

                relative_path = (
                    (relative_path + "/" + new_node.path_template)
                    if new_node.path_template
                    else relative_path
                )

                new_node.path = relative_path
                # register static route
                if new_node.is_static or new_node.is_root:
                    self.route_registry.register_root_route(new_node)

                elif new_node.is_slot:
                    current_node.register_slot(new_node)
                else:
                    current_node.register_route(new_node)

        # Process subdirectories
        for entry in sorted(entries):
            if entry.startswith((".", "_")) or entry == "page.py":
                continue

            full_path = os.path.join(current_dir, entry)
            if os.path.isdir(full_path):
                # If we don't have a page.py, pass the current_node down
                # Otherwise, use the new_node we created
                next_node = new_node if dir_has_page else current_node
                self._traverse_directory(current_dir, entry, next_node)

    def load_route_module(
        self, current_dir: str, segment: str, parent_node: PageNode
    ) -> PageNode:
        module_path = os.path.join(current_dir, "page.py")
        module_path_parts = os.path.splitext(module_path)[0].split(os.sep)
        module_name = ".".join(module_path_parts)

        # Route is at top level when there is no parent or the parent is the root
        is_root = parent_node.segment == "/" or not parent_node.segment
        segment = "/" if not parent_node.segment else segment

        try:
            # Import the module
            page_module = importlib.import_module(module_name)
            layout = getattr(page_module, "layout", None)

            if layout is None:
                raise ImportError(
                    f"Module {module_name} needs a layout function or component"
                )

            route_config: RouteConfig = getattr(page_module, "config", RouteConfig())
            is_slot = segment.startswith("(") and segment.endswith(")")

            new_node = PageNode(
                layout=layout,
                segment=segment.strip("()"),
                parent_segment=parent_node.segment,
                module=module_name,
                is_slot=is_slot,
                is_static=route_config.is_static,
                is_root=is_root,
            )

            new_node.load_config(route_config)

            return new_node

        except ImportError as e:
            print(f"Import Error in {module_name}: {e}")
            print(f"Traceback: {traceback.format_exc()}")

        except Exception as e:
            print(f"Error processing {module_name}: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    def strip_relative_path(self, path: str):
        return app_strip_relative_path(self.app.config.requests_pathname_prefix, path)

    def get_static_route(self, path: str):
        path_variables = None

        for root_page in self.route_registry.routes.values():
            if not root_page.is_static:
                continue

            if root_page.path_template:
                path_variables = _parse_path_variables(path, root_page.path)
                if path_variables:
                    return root_page, path_variables

            if path == root_page.path:
                return root_page, path_variables

        return None, path_variables

    def _get_root_node(
        self, segments: List[str], loading_state: Dict[str, bool]
    ) -> Tuple[Optional["PageNode"], List[str], Optional[str]]:
        remaining_segments = segments.copy()
        updated_segments = {}
        variables = {}
        active_root_node = None

        while remaining_segments:
            current_segment = remaining_segments[0]

            if not active_root_node:
                active_root_node = self.route_registry.get_route(current_segment)

                if not active_root_node:
                    return None, [], {}, {}

                loading_state_key = (
                    create_pathtemplate_key(
                        active_root_node.segment,
                        active_root_node.path_template,
                        current_segment,
                        active_root_node.path_template.strip("<>"),
                    )
                    if active_root_node.path_template
                    else current_segment
                )
                remaining_segments.pop(0)

                if not loading_state.get(loading_state_key, False):
                    return (
                        active_root_node,
                        remaining_segments,
                        updated_segments,
                        variables,
                    )
                updated_segments[loading_state_key] = True
                continue

            current_node = active_root_node.get_child_node(current_segment)

            if not current_node:
                if not self.ignore_empty_folders and len(remaining_segments) > 0:
                    next_segment = remaining_segments.pop(0)
                    concat_segment = f"{current_segment}/{next_segment}"
                    remaining_segments.insert(0, concat_segment)
                    continue

                remaining_segments.pop(0)
                continue
            # handle loading state
            loading_state_key = (
                create_pathtemplate_key(
                    current_node.segment,
                    current_node.path_template,
                    current_segment,
                    current_node.path_template.strip("<>"),
                )
                if current_node.path_template
                else current_segment
            )

            active_root_node = current_node
            if not loading_state.get(loading_state_key, False):
                if current_node.segment == loading_state_key:
                    remaining_segments.pop(0)

                return active_root_node, remaining_segments, updated_segments, variables

            if current_node.path_template:
                if len(remaining_segments) == 1:
                    return (
                        active_root_node,
                        remaining_segments,
                        updated_segments,
                        variables,
                    )

                variables[current_node.path_template.strip("<>")] = current_segment

            updated_segments[loading_state_key] = True
            remaining_segments.pop(0)

        return active_root_node, remaining_segments, updated_segments, variables

    def build_execution_tree(
        self,
        current_node: PageNode,
        segments: List[str],
        parent_variables: Dict[str, str],
        query_params: Dict[str, any],
        loading_state: Dict[str, bool],
    ) -> Optional[ExecNode]:
        current_variables = parent_variables.copy()
        next_segment = segments[0] if segments else None

        if current_node.path_template and next_segment:
            varname = current_node.path_template.strip("<>")
            current_variables[varname] = next_segment
            segments = segments[1:]
            next_segment = segments[0] if segments else None

        exec_node = ExecNode(
            layout=current_node.layout,
            segment=current_node.segment,
            parent_segment=current_node.parent_segment,
            variables=current_variables,
            loading_state=loading_state,
            path_template=current_node.path_template,
        )

        if current_node.child_nodes:
            child_node = current_node.child_nodes.get(next_segment)

            if not child_node:
                default_segment = current_node.default_child
                child_node = current_node.child_nodes.get(default_segment, None)

            # Pass down the current_variables to the child
            segments = segments[1:]
            child_exec_node = (
                self.build_execution_tree(
                    current_node=child_node,
                    segments=segments.copy(),
                    loading_state=loading_state,
                    parent_variables=current_variables,
                    query_params=query_params,
                )
                if child_node
                else None
            )

            exec_node.child_node["children"] = child_exec_node

            if not segments:
                return exec_node

        if current_node.slots:
            for slot_name, slot_node in current_node.slots.items():
                slot_exec_node = self.build_execution_tree(
                    current_node=slot_node,
                    segments=segments.copy(),
                    parent_variables=current_variables,
                    loading_state=loading_state,
                    query_params=query_params,
                )

                exec_node.slots[slot_name] = slot_exec_node

            if not segments:
                return exec_node

        return exec_node

    def setup_router(self):
        @self.app.server.before_request
        async def router():
            request_data = await request.get_data()

            if not request_data:
                return

            body = json.loads(request_data)
            changed_prop = body["changedPropIds"]

            # I expect '[dash-router-location.pathname]'
            changed_prop_id = changed_prop[0].split(".")[0] if changed_prop else None

            # Pass if the current request is not by our location
            if changed_prop_id != RootContainer.ids.location:
                return

            inputs = body.get("inputs", [])
            state = body.get("state", [])

            args = inputs_to_vals(inputs + state)

            pathname_, search_, loading_state_ = args

            query_parameters = _parse_query_string(search_)

            # Handle root path specially
            if pathname_ == "/" or not pathname_:
                node = self.route_registry.get_route("/")
                layout = await node.layout(**query_parameters)
                return {
                    "multi": True,
                    "response": {
                        RootContainer.ids.container: {
                            "children": recursive_to_plotly_json(layout)
                        },
                    },
                }

            path = self.strip_relative_path(pathname_)

            # handle roote and check for static routes
            static_route, path_variables = self.get_static_route(path)
            if static_route:
                layout = await static_route.layout(
                    **query_parameters, **path_variables or {}
                )

                return {
                    "multi": True,
                    "response": {
                        RootContainer.ids.container: {
                            "children": recursive_to_plotly_json(layout)
                        },
                    },
                }

            # segment wise tree search
            init_segments = [
                segment for segment in pathname_.strip("/").split("/") if segment
            ]

            active_root_node, remaining_segments, updated_segments, path_variables = (
                self._get_root_node(init_segments, loading_state_)
            )

            if not active_root_node:
                return {
                    "multi": True,
                    "response": {
                        RootContainer.ids.container: {
                            "children": recursive_to_plotly_json(
                                html.H1("404 - Page not found")
                            )
                        },
                    },
                }

            exec_tree = self.build_execution_tree(
                current_node=active_root_node,
                segments=remaining_segments,
                parent_variables=path_variables,  # Start with empty variables
                query_params=query_parameters,
                loading_state=updated_segments,
            )

            if not exec_tree:
                return {
                    "multi": True,
                    "response": {
                        RootContainer.ids.container: {
                            "children": recursive_to_plotly_json(
                                html.H1("404 - Page not found")
                            )
                        },
                    },
                }

            final_layout = await exec_tree.execute()
            new_loading_state = {**updated_segments, **exec_tree.loading_state}
            container_id = RootContainer.ids.container

            if active_root_node.parent_segment != "/":
                if active_root_node.is_slot:
                    container_id = json.dumps(
                        SlotContainer.ids.container(
                            active_root_node.parent_segment,
                            active_root_node.segment,
                        )
                    )

                else:
                    container_id = json.dumps(
                        ChildContainer.ids.container(
                            active_root_node.parent_segment,
                        )
                    )

            return {
                "multi": True,
                "response": {
                    container_id: {"children": recursive_to_plotly_json(final_layout)},
                    RootContainer.ids.state_store: {"data": new_loading_state},
                },
            }

        @self.app.server.before_serving
        async def trigger_router():
            inputs = {
                "pathname_": Input(RootContainer.ids.location, "pathname"),
                "search_": Input(RootContainer.ids.location, "search"),
                "loading_state_": State(RootContainer.ids.state_store, "data"),
            }

            inputs.update(self.app.routing_callback_inputs)

            @self.app.callback(
                Output(RootContainer.ids.dummy, "children"), inputs=inputs
            )
            async def update(
                pathname_: str, search_: str, loading_state_: str, **states
            ):
                return
