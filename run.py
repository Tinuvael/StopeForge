import sys


APP_VERSION = "0.1.0"


def run_smoke_test() -> None:
    """
    Minimal packaged-app check.
    Does not open GUI.
    """
    from db.schema import initialize_database

    initialize_database()

    print(f"StopeForge {APP_VERSION} smoke test OK")


def run_gui() -> None:
    """
    Normal GUI startup:
    splash -> main app.
    """
    from app.splash import show_splash
    from app.main_window import StopeForgeApp

    show_splash()

    app = StopeForgeApp()
    app.mainloop()


if __name__ == "__main__":
    if "--version" in sys.argv:
        print(f"StopeForge {APP_VERSION}")
        sys.exit(0)

    if "--smoke-test" in sys.argv:
        run_smoke_test()
        sys.exit(0)

    run_gui()
