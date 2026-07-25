from types import SimpleNamespace

from gui.case_histories_tab import ALL_VALUE, CaseHistoriesTab
from gui.stability_graph_tab import StabilityGraphTab


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeTree:
    def __init__(self):
        self.removed = None

    def selection(self):
        return ("selected-row",)

    def selection_remove(self, selection):
        self.removed = selection


def test_graph_source_can_get_all_cases_despite_case_history_filter():
    tab = SimpleNamespace(
        rows=[
            {"project": "Mine A", "domain": "D1", "surface": "Crown", "observed_state": "Stable"},
            {"project": "Mine B", "domain": "D2", "surface": "Footwall", "observed_state": "Caved"},
        ],
        project_filter_var=FakeVar("Mine A"),
        domain_filter_var=FakeVar(ALL_VALUE),
        surface_filter_var=FakeVar(ALL_VALUE),
        observed_filter_var=FakeVar(ALL_VALUE),
    )

    filtered = CaseHistoriesTab.get_filtered_rows(tab)
    all_rows = CaseHistoriesTab.get_all_rows(tab)

    assert len(filtered) == 1
    assert len(all_rows) == 2
    assert all_rows is not tab.rows


def test_case_history_clear_filters_shows_everything_and_clears_selection():
    refreshed = []
    tab = SimpleNamespace(
        project_filter_var=FakeVar("Mine A"),
        domain_filter_var=FakeVar("D1"),
        surface_filter_var=FakeVar("Crown"),
        observed_filter_var=FakeVar("Stable"),
        observed_state_var=FakeVar("Stable"),
        comment_var=FakeVar("note"),
        tree=FakeTree(),
        selected_item_id="selected-row",
        refresh_table=lambda: refreshed.append(True),
    )

    CaseHistoriesTab.clear_filters(tab)

    assert tab.project_filter_var.get() == ALL_VALUE
    assert tab.domain_filter_var.get() == ALL_VALUE
    assert tab.surface_filter_var.get() == ALL_VALUE
    assert tab.observed_filter_var.get() == ALL_VALUE
    assert tab.selected_item_id is None
    assert tab.tree.removed == ("selected-row",)
    assert refreshed == [True]


def test_graph_clear_filters_resets_all_filters_before_redraw():
    calls = []
    tab = SimpleNamespace(
        project_filter_var=FakeVar("Mine A"),
        domain_filter_var=FakeVar("D1"),
        surface_filter_var=FakeVar("Crown"),
        observed_filter_var=FakeVar("Stable"),
        saved_boundary_var=FakeVar("Old boundary"),
        saved_boundaries=[{"boundary_name": "Old boundary"}],
        refresh_filter_lists=lambda: calls.append("lists"),
        refresh_graph=lambda **kwargs: calls.append(("graph", kwargs)),
    )

    StabilityGraphTab.clear_filters(tab)

    assert tab.project_filter_var.get() == ALL_VALUE
    assert tab.domain_filter_var.get() == ALL_VALUE
    assert tab.surface_filter_var.get() == ALL_VALUE
    assert tab.observed_filter_var.get() == ALL_VALUE
    assert tab.saved_boundary_var.get() == ""
    assert tab.saved_boundaries == []
    assert calls == ["lists", ("graph", {"load_active_boundary": False})]
