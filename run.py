import sys

from app.main_window import main as run_main_window


APP_VERSION = "0.9.0"


def run_smoke_test():
    print("StopeForge smoke test OK")


def run_gui():
    try:
        from app.splash import show_splash
        show_splash()
    except Exception as error:
        print(f"Splash skipped: {error}")

    run_main_window()


if __name__ == "__main__":
    if "--version" in sys.argv:
        print(f"StopeForge {APP_VERSION}")
        sys.exit(0)

    if "--smoke-test" in sys.argv:
        run_smoke_test()
        sys.exit(0)

    run_gui()
