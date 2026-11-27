import pytest
from dash import dcc

import dash_router
from dash_router import ChildContainer, UrlSegment


def test_base_and_active_come_from_container():
    tabs = dcc.Tabs(id="tabs")
    segment = UrlSegment(tabs, ChildContainer(active="timeline", base="/orders/1003"))

    assert getattr(segment, "base") == "/orders/1003"
    assert getattr(tabs, "value") == "timeline"


def test_explicit_base_wins_over_container():
    segment = UrlSegment(dcc.Tabs(id="tabs"), ChildContainer(base="/orders/1003"), base="/orders/9")

    assert getattr(segment, "base") == "/orders/9"


def test_base_only_without_container():
    segment = UrlSegment(dcc.Tabs(id="tabs"), base="/orders/1003")

    assert getattr(segment, "base") == "/orders/1003"


def test_missing_base_raises():
    with pytest.raises(ValueError):
        UrlSegment(dcc.Tabs(id="tabs"), ChildContainer())


def test_missing_base_without_container_raises():
    with pytest.raises(ValueError):
        UrlSegment(dcc.Tabs(id="tabs"))


def test_root_base_is_empty_string():
    segment = UrlSegment(dcc.Tabs(id="tabs"), ChildContainer(base=""))

    assert getattr(segment, "base") == ""


def test_active_none_falls_back_to_default():
    tabs = dcc.Tabs(id="tabs")
    UrlSegment(tabs, ChildContainer(base="/orders/1003"), default="overview")

    assert getattr(tabs, "value") == "overview"


def test_existing_value_is_kept():
    tabs = dcc.Tabs(id="tabs", value="notes")
    UrlSegment(tabs, ChildContainer(active="timeline", base="/orders/1003"))

    assert getattr(tabs, "value") == "notes"


def test_value_not_set_without_container():
    tabs = dcc.Tabs(id="tabs")
    UrlSegment(tabs, base="/orders/1003", default="overview")

    assert getattr(tabs, "value", None) is None


def test_props_are_serialized():
    segment = UrlSegment(
        dcc.Tabs(id="tabs"),
        ChildContainer(base="/orders/1003"),
        prop="value",
        default="overview",
        history="replace",
        keep_query=False,
    )
    props = segment.to_plotly_json()["props"]

    assert props["base"] == "/orders/1003"
    assert props["prop"] == "value"
    assert props["default"] == "overview"
    assert props["history"] == "replace"
    assert props["keepQuery"] is False


def test_keep_query_and_history_defaults():
    props = UrlSegment(dcc.Tabs(id="tabs"), base="/x").to_plotly_json()["props"]

    assert props["history"] == "push"
    assert props["keepQuery"] is True
    assert "default" not in props


def test_children_is_the_wrapped_component():
    tabs = dcc.Tabs(id="tabs")
    segment = UrlSegment(tabs, base="/x")

    assert segment.children is tabs


def test_exported_from_package():
    assert dash_router.UrlSegment is UrlSegment
    assert "UrlSegment" in dash_router.__all__
