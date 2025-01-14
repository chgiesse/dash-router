from .models import PageNode, RootNode, RouteConfig, ExecNode
from .components import RootContainer, ChildContainer
from typing import Dict, List, Optional, Union, Callable
from dash.development.base_component import Component
from flash._pages import _parse_query_string, _parse_path_variables
from dash import Dash, html
from dash._get_paths import app_strip_relative_path
from flash import Flash, Input, Output, State, no_update, strip_relative_path, set_props
from typing import Union
from dataclasses import dataclass
import importlib
import traceback
import os
import asyncio


from dataclasses import dataclass, field
from typing import Dict, Optional, Union, Callable, Tuple
import asyncio


class Router:

    def __init__(
        self, 
        app: Union[Dash, Flash], 
        pages_folder: str = 'pages',
        requests_pathname_prefix: str = None,
        ignore_empty_folders: bool = False
    ) -> None:

        self.app = app
        self.route_registry = RootNode()
        self.requests_pathname_prefix = requests_pathname_prefix
        self.ignore_empty_folders = ignore_empty_folders
        self.pages_folder = (
            app.pages_folder
            if app.pages_folder 
            else pages_folder
        )

        if isinstance(self.app, Dash):
            self.is_async = False
        elif isinstance(self.app, Flash):
            self.is_async = True
        else:
            raise TypeError(f'App needs to be of type Dash or flash not: {type(self.app)}')
        
        self.setup_route_tree()

        self.setup_router()


    def setup_route_tree(self) -> None:
        root_dir = '.'.join(self.app.server.name.split(os.sep)[:-1])
        self._traverse_directory(root_dir, self.pages_folder, self.route_registry)


    def _traverse_directory(self, parent_dir: str, segment: str, current_node: Union[RootNode, PageNode]):
        current_dir = os.path.join(parent_dir, segment)
        if not os.path.exists(current_dir):
            return
        
        entries = os.listdir(current_dir)
        dir_has_page = 'page.py' in entries

        if dir_has_page:
            new_node = self.load_route_module(current_dir, segment, current_node.segment)
            # Set the path based on the directory structure
            if current_dir == self.pages_folder:
                new_node.path = '/'
                new_node.segment = '/'
                new_node.parent_segment = None
                self.route_registry.register_root_route(new_node)
            
            else:
                # print(current_dir, segment, new_node.parent_segment)
                # Remove the base directory from the path
                relative_path = os.path.relpath(current_dir, self.pages_folder)
                new_node.path = relative_path

                register_at_root = True

                if isinstance(current_node, PageNode):
                    if current_node.view_template:
                        # print(current_node.view_template)
                        current_node.register_route(new_node)
                        register_at_root = False
                    
                    if new_node.is_slot:
                        current_node.register_slot(new_node)
                        register_at_root = False

                # register static route
                if register_at_root:
                    self.route_registry.register_root_route(new_node)
                
        # Process subdirectories
        for entry in sorted(entries):
            if entry.startswith(('.', '_')) or entry == 'page.py':
                continue
            
            full_path = os.path.join(current_dir, entry)
            if os.path.isdir(full_path): 
                # If we don't have a page.py, pass the current_node down
                # Otherwise, use the new_node we created
                next_node = new_node if dir_has_page else current_node
                self._traverse_directory(current_dir, entry, next_node)


    def load_route_module(self, current_dir: str, segment: str, parent_segment: str) -> PageNode:

        module_path = os.path.join(current_dir, 'page.py')
        module_path_parts = os.path.splitext(module_path)[0].split(os.sep)
        module_name = '.'.join(module_path_parts)

        # Route is at top level when there is no parent or the parent is the root 
        is_root = parent_segment == '/' or not parent_segment 
        segment = '/' if not parent_segment else segment

        try:
            # Import the module
            page_module = importlib.import_module(module_name)
            layout = getattr(page_module, "layout", None)
            
            if layout is None:
                raise ImportError(f'Module {module_name} needs a layout function or component')
            
            route_config: RouteConfig = getattr(page_module, 'config', RouteConfig())
            is_slot = segment.startswith('(') and segment.endswith(')')
            is_static = not is_slot and not route_config.view_template
            cleaned_segment = segment.strip('()')

            new_node = PageNode(
                layout=layout,
                segment=cleaned_segment,
                parent_segment=parent_segment,
                module=module_name,
                is_slot=is_slot,
                is_static=is_static,
                is_root=is_root
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
                template_id = os.path.join(root_page.path, root_page.path_template).strip('/')
                path_variables = _parse_path_variables(path, template_id)
                if path_variables:
                    return root_page, path_variables
            
            if path == root_page.path:
                return root_page, path_variables
            
        return None, path_variables
    

    def _get_root_node(
        self, 
        segments: List[str], 
        loading_state: Dict[str, bool]
    ) -> Tuple[Optional['PageNode'], List[str], Optional[str]]:
        '''
        Finds the root node of a dynamic route which gets traversed.
        Now also returns the active parent segment.

        :param segments: List of URL path segments.
        :param loading_state: Dictionary indicating which segments should be skipped.
        :return: A tuple containing the root PageNode (or None if not found),
                the remaining segments, and the active parent segment (str or None).
        '''
        remaining_segments = segments.copy()
        active_root_node = None

        while remaining_segments:
            # Pop the first segment
            current_segment = remaining_segments[0]

            if active_root_node is None:
                print('FIRST ROUTE FOUND: ', current_segment)
                active_root_node = self.route_registry.get_route(current_segment)
                remaining_segments = remaining_segments[1:]
                
            # Check if the current segment should be skipped based on loading_state
            if loading_state.get(current_segment, False):
                print(f"Segment '{current_segment}' is active and will be skipped.")
                if remaining_segments:
                    # Pop the next segment to traverse
                    next_segment = remaining_segments[0]
                    print(f"Traversing to next segment: '{current_segment}'")
                    next_node = active_root_node.get_child_node(next_segment)
                    if next_node:
                        print(f"Found child node for segment '{next_segment}'")
                        active_root_node = next_node
                        remaining_segments = remaining_segments[1:]
                        continue
                    else:
                        print(f"No child node found for segment '{next_segment}'.")
                        return None, remaining_segments
                else:
                    # No more segments to traverse
                    return active_root_node, remaining_segments

            # If segment is not marked for skipping, return the current node
            if active_root_node:
                if active_root_node.path_template:
                    print(f"Found root_route for segment: '{current_segment}'")
                    remaining_segments = [current_segment, *remaining_segments]
                
                return active_root_node, remaining_segments

            # Handle concatenation if necessary
            if not self.ignore_empty_folders and len(remaining_segments) > 0:
                next_segment = remaining_segments.pop(0)
                concat_segment = f"{current_segment}/{next_segment}"
                remaining_segments.insert(0, concat_segment)
                print(f"Concatenated segments: '{concat_segment}'")
                continue

            # If no route is found and concatenation isn't possible, exit
            print(f"Cannot concatenate segments or ignore_empty_folders=True. Exiting loop.")
            return None, remaining_segments

        # After processing all segments, return the active_root_node and active_parent if set
        if active_root_node:
            print('Return root node: ', current_segment)
            return active_root_node, remaining_segments

        return None, remaining_segments


            
    def build_execution_tree(
        self,
        current_node: PageNode,
        segments: List[str],
        parent_variables: Dict[str, str],
        query_params: Dict[str, any],
        loading_state: Dict[str, bool]
    ) -> Optional[ExecNode]:

        """
        Recursively builds the execution tree based on the URL segments.

        :param current_node: The current PageNode being processed.
        :param segments: The remaining URL path segments to process.
        :param loading_state: Current loading state to handle async operations.
        :param query_params: Query parameters from the URL.
        :return: An ExecNode representing the root of the execution tree, or None if not found.
        """
        
        current_variables = parent_variables.copy()
        next_segment = segments[0] if segments else None
        
        # handle path template
        if current_node.path_template and next_segment:
            varname = current_node.path_template.strip('<>')
            current_variables[varname] = next_segment
            print(f"Extracted variable: {varname} = {next_segment}")
            segments = segments[1:]
            next_segment = segments[0] if segments else None

        exec_node = ExecNode(
            layout=current_node.layout,
            segment=current_node.segment,
            parent_segment=current_node.parent_segment,
            variables=current_variables,
            loading_state=loading_state,
        )

        IS_MATCHED = False

        # Handle parallel routes
        if current_node.view_template:

            varname = current_node.view_template.strip('[]')
            view_node = current_node.parallel_routes.get(next_segment)

            if not view_node:
                print(f"No matching view for segment: {next_segment}")
                exec_node.views[varname] = None
            
            else:
                print(f"Traversing to view: {next_segment} with segments left: {segments} and template: {view_node.path_template}")
                # Pass down the current_variables to the child
                print('PARENT: ', current_node.parent_segment, 'BECOMES PARENT: ', current_node.segment)
                segments = segments[1:]
                child_exec_node = self.build_execution_tree(
                    current_node=view_node,
                    segments=segments.copy(),
                    loading_state=loading_state,
                    parent_variables=current_variables,
                    query_params=query_params
                )

                exec_node.views[varname] = child_exec_node
                IS_MATCHED = True

        if current_node.slots:
            for slot_name, slot_node in current_node.slots.items():
                print(f"Traversing to slot: {slot_name} with var: {segments}")

                slot_exec_node = self.build_execution_tree(
                    current_node=slot_node,
                    segments=segments.copy(),
                    parent_variables=current_variables,
                    loading_state=loading_state,
                    query_params=query_params
                )
                
                exec_node.slots[slot_name] = slot_exec_node
        
        return exec_node

    
    def setup_router(self):

        @self.app.server.before_serving
        async def router():

            inputs = {
                'pathname_': Input(RootContainer.ids.location, 'pathname'),
                'search_': Input(RootContainer.ids.location, 'search'),
                'loading_state_': State(RootContainer.ids.state_store, 'data')
            }

            inputs.update(self.app.routing_callback_inputs)

            @self.app.callback(
                Output(RootContainer.ids.container, 'children'),
                Output(RootContainer.ids.state_store, 'data'),
                inputs=inputs
            )

            async def update(pathname_: str, search_: str, loading_state_: str, **states):
                query_parameters = _parse_query_string(search_)

                # Handle root path specially
                if pathname_ == '/' or not pathname_:
                    node = self.route_registry.get_route('/')
                    layout = await node.layout(**states, **query_parameters)
                    return layout, no_update
                
                path = self.strip_relative_path(pathname_)

                #handle roote and check for static routes
                static_route, path_variables = self.get_static_route(path)       
     
                if static_route:
                    return await static_route.layout(**query_parameters, **path_variables or {}), no_update
                
                # segment wise tree search 
                init_segments = [segment for segment in pathname_.strip('/').split('/') if segment]
                active_root_node, remaining_segments = self._get_root_node(init_segments, loading_state_)
                print('rem segments: ', remaining_segments)
                # print('Active root parent: ', active_root_parent)   
                if not active_root_node:
                    return html.H1('404 - Page not found'), {}

                exec_tree = self.build_execution_tree(
                    current_node=active_root_node,
                    segments=remaining_segments,
                    parent_variables={},  # Start with empty variables
                    query_params=query_parameters,
                    loading_state=loading_state_
                )

                if not exec_tree:
                    return html.H1('404 - Page not found'), {}
                
                final_layout = await exec_tree.execute()
                # clean loading store
                new_loading_state = {segment: state for segment, state in exec_tree.loading_state.items() if segment in init_segments}
            

                # if we dont render the root segment we use setprops to insert into the parent
                if active_root_node.parent_segment != '/':
                    set_props(
                        ChildContainer.ids.container(active_root_node.parent_segment), 
                        {'children': final_layout}
                    )
                    return no_update, new_loading_state

                # Execute the tree to get the final layout
                print('UPDATED LOADINGSTATE: ', new_loading_state)
                return final_layout, new_loading_state
