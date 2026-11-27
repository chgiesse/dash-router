from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .core.execution import PatchUpdate, execute_plan
from .core.matcher import TransitionPlan, plan_transition
from .core.tree import RouteTree
from .router import DashRouter
from .types import RenderMode


@dataclass(frozen=True)
class TransitionResult:
    """Inspection & assertion handle returned by `RouteTester.transition(old, new)`."""

    tree: RouteTree
    plan: TransitionPlan

    @property
    def matched(self) -> bool:
        return self.plan.matched

    @property
    def segments(self) -> list[str]:
        """Node ids rendered by the transition."""
        return self.plan.segments

    @property
    def targets(self) -> list[str | dict[str, str]]:
        """Container ids patched by the transition."""
        return self.plan.targets

    @property
    def modes(self) -> dict[str, RenderMode]:
        """Render mode (`page`, `default` or `empty`) of every touched node."""
        return self.plan.modes

    @property
    def vars(self) -> dict[str, dict[str, Any]]:
        """Variables (`{**query_params, **path_vars}`) passed to each rendered node."""
        return self.plan.node_vars

    def vars_for(self, node_id: str) -> dict[str, Any]:
        return self.vars[node_id]

    async def render(self) -> list[PatchUpdate]:
        return await execute_plan(self.tree, self.plan)


class RouteTester:
    """`(old_url, new_url) -> expected segments` test harness for a `DashRouter` or `RouteTree`."""

    def __init__(self, target: DashRouter | RouteTree) -> None:
        self.tree: RouteTree = target.tree if isinstance(target, DashRouter) else target

    @classmethod
    def from_spec(cls, spec: Mapping[str, Any]) -> "RouteTester":
        return cls(RouteTree.from_spec(spec))

    @classmethod
    def from_folder(cls, pages_folder: str | Path, ignore_empty_folders: bool = False) -> "RouteTester":
        return cls(RouteTree.from_folder(pages_folder, ignore_empty_folders=ignore_empty_folders))

    def transition(
        self,
        old: str | None,
        new: str,
        *,
        extra_inputs: Mapping[str, Any] | None = None,
        prev_extra_inputs: Mapping[str, Any] | None = None,
    ) -> TransitionResult:
        return TransitionResult(self.tree, plan_transition(self.tree, old, new, extra_inputs, prev_extra_inputs))

    def assert_routes(
        self,
        old: str | None,
        new: str,
        expected: Iterable[str],
        *,
        ordered: bool = False,
        extra_inputs: Mapping[str, Any] | None = None,
        prev_extra_inputs: Mapping[str, Any] | None = None,
        expected_modes: Mapping[str, RenderMode] | None = None,
        expected_vars: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> TransitionResult:
        result = self.transition(old, new, extra_inputs=extra_inputs, prev_extra_inputs=prev_extra_inputs)
        label = f"Transition {old!r} -> {new!r}"
        _check_segments(result, list(expected), ordered, label)
        for node_id, mode in (expected_modes or {}).items():
            _check_equal(result.modes.get(node_id), mode, f"{label} mode of '{node_id}' (all: {result.modes})")
        for node_id, variables in (expected_vars or {}).items():
            if node_id not in result.vars:
                raise AssertionError(f"{label}: '{node_id}' was not rendered (rendered: {result.segments})")
            actual = result.vars[node_id]
            for key, value in variables.items():
                _check_equal(actual.get(key), value, f"{label} var '{node_id}[{key!r}]' (all: {actual})")
        return result


def assert_transition(
    target: DashRouter | RouteTree | RouteTester,
    old: str | None,
    new: str,
    expected: Iterable[str],
    **checks: Any,
) -> TransitionResult:
    """Shortcut for `RouteTester(target).assert_routes(old, new, expected, **checks)`."""
    tester = target if isinstance(target, RouteTester) else RouteTester(target)
    return tester.assert_routes(old, new, expected, **checks)


def _check_segments(result: TransitionResult, expected: list[str], ordered: bool, label: str) -> None:
    actual = result.segments
    if len(actual) != len(set(actual)):
        raise AssertionError(f"{label} rendered duplicate segments: {actual}")
    if ordered:
        _check_equal(actual, expected, f"{label} segment order (targets: {result.targets})")
    elif set(actual) != set(expected):
        raise AssertionError(
            f"{label} segments mismatch:\n"
            f"  missing:    {sorted(set(expected) - set(actual))}\n"
            f"  unexpected: {sorted(set(actual) - set(expected))}\n"
            f"  matched:    {result.matched}\n"
            f"  targets:    {result.targets}"
        )


def _check_equal(actual: Any, expected: Any, what: str) -> None:
    if actual != expected:
        raise AssertionError(f"{what}: expected {expected!r}, got {actual!r}")
