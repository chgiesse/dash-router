# Catch-All Route Tests Plan

## Goal
Validate catch-all routing behavior using data structures only (active node,
execution tree, and routing context) without rendering layouts or running a
server.

## Scope
- Catch-all routes (`[__rest]`) with deep paths and root paths.
- Active node semantics: active node remains the parent branch that is already
  rendered; catch-all renders as the leaf layout within that branch.
- Path variable extraction for `rest` and other path params (e.g., `team_id`).

## Approach
1) **Core-level tests only**
   - Use `RoutingContext`, `RouteTree.get_active_root_node`, and
     `Router.build_execution_tree`.
   - Avoid layout execution and server setup.

2) **Use the deep team/files catch-all example**
   - `projects/[team_id]/files/[__rest]` in `tests/pages`.

3) **Reset static registries per test**
   - Clear `RouteTable` and `RouteTree` static state in an autouse fixture to
     prevent cross-test pollution.

4) **Assert active node and leaf node**
   - Active node is the already-rendered parent (`.../files`).
   - Exec tree leaf is the catch-all node (`[__rest]`).

5) **Include empty-rest cases**
   - `/projects/alpha/files` should yield `rest == []`.

6) **Cover root catch-all**
   - `/files/1/2/3` should yield `rest == ["1", "2", "3"]` and keep `files` as
     active node.

## Proposed Test Cases
- `/projects/alpha/files`
  - active node: `projects/[team_id]/files`
  - `ctx.path_vars["team_id"] == "alpha"`
  - `ctx.path_vars["rest"] == []`
  - exec tree leaf: `projects/[team_id]/files/[__rest]`

- `/projects/alpha/files/1`
  - active node: `projects/[team_id]/files`
  - `ctx.path_vars["rest"] == ["1"]`
  - exec tree leaf: `projects/[team_id]/files/[__rest]`

- `/projects/alpha/files/1/2/3`
  - active node: `projects/[team_id]/files`
  - `ctx.path_vars["rest"] == ["1", "2", "3"]`
  - exec tree leaf: `projects/[team_id]/files/[__rest]`

- `/files/1/2/3`
  - active node: `files`
  - `ctx.path_vars["rest"] == ["1", "2", "3"]`
  - exec tree leaf: `files/[__rest]`

# Nested + Slot Route Tests Plan

## Goal
Validate nested route behavior combined with slots and nested slots using data
structures only (active node, execution tree, and routing context) without
rendering layouts or running a server.

## Scope
- Nested route selection for `/tickets/[ticket_id]`.
- Slot rendering under a nested route: `(detail)` and `(activity)`.
- Nested slot resolution within slots: `(summary)` and `(comments)`.
- Path variable propagation for `ticket_id` across nested and slot branches.

## Approach
1) **Core-level tests only**
   - Use `RoutingContext`, `RouteTree.get_active_root_node`, and
     `Router.build_execution_tree`.
   - Avoid layout execution and server setup.

2) **Use the tickets example**
   - `tickets/[ticket_id]/(detail)/(summary)` and
     `tickets/[ticket_id]/(activity)/(comments)` in `tests/pages`.

3) **Reset static registries per test**
   - Clear `RouteTable` and `RouteTree` static state in an autouse fixture to
     prevent cross-test pollution.

4) **Assert active node and slot leaves**
   - Active node remains the nested route (`tickets/[ticket_id]`).
   - Exec tree includes both slot branches; leaf nodes reflect `summary` and
     `comments` when requested.

## Proposed Test Cases
- `/tickets`
  - active node: `tickets`
  - exec tree leaf: `tickets`

- `/tickets/1001`
  - active node: `tickets/[ticket_id]`
  - `ctx.path_vars["ticket_id"] == "1001"`
  - exec tree includes slot leaves:
    - `tickets/[ticket_id]/(detail)`
    - `tickets/[ticket_id]/(activity)`

- `/tickets/1001`
  - active node: `tickets/[ticket_id]`
  - `ctx.path_vars["ticket_id"] == "1001"`
  - exec tree includes nested slots:
    - `tickets/[ticket_id]/(detail)/(summary)`
    - `tickets/[ticket_id]/(activity)/(comments)`
