def test_core_imports():
    import core.models
    import core.mathews_factors
    import core.stability
    import core.local_assessment
    import core.export_excel


def test_db_imports():
    import db.connection
    import db.schema
    import db.case_repository
    import db.boundary_repository


def test_gui_imports():
    import app.main_window
    import gui.calculation_tab
    import gui.case_histories_tab
    import gui.project_overview_tab
    import gui.stability_graph_tab
