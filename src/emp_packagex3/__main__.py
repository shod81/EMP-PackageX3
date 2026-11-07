"""CLI / GUI entry point for EMP-PackageX3.

Positional arguments are Setup.inf file paths – they make the Explorer
"Open with" file association work (the shell passes the document as argv).
"""

from __future__ import annotations

import sys

_USAGE = """EMP-PackageX3 - Matrix42 Empirum PackageCreator & PackageEditor

Verwendung: emp-packagex3 [OPTIONEN] [SETUP.INF]

Setup.inf direkt oeffnen (auch via Explorer 'Oeffnen mit'):
  emp-packagex3 C:\\Paket\\Install\\Setup.inf

Optionen:
  --debug     ausfuehrliches Logging (zusaetzlich zur Einstellung)
  --version   Version ausgeben und beenden
  -h, --help  diese Hilfe ausgeben und beenden
"""

_KNOWN_FLAGS = {"--debug", "--version", "-V", "--help", "-h"}


def split_cli_args(args: list[str]) -> tuple[list[str], list[str]]:
    """Split argv into positional file paths and unrecognized flags."""
    positional = [a for a in args if not a.startswith("-")]
    unknown = [a for a in args if a.startswith("-") and a not in _KNOWN_FLAGS]
    return positional, unknown


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--version" in args or "-V" in args:
        from emp_packagex3 import APP_NAME, COPYRIGHT, __version__

        print(f"{APP_NAME} {__version__}")
        print(COPYRIGHT)
        return 0
    if "--help" in args or "-h" in args:
        print(_USAGE, end="")
        return 0

    debug = "--debug" in args
    rest = [a for a in args if a != "--debug"]
    positional, unknown = split_cli_args(rest)
    if unknown:
        print(f"Unbekannte Argumente: {' '.join(unknown)}", file=sys.stderr)
        print(_USAGE, end="", file=sys.stderr)
        return 2

    from pathlib import Path

    from emp_packagex3.logging_setup import setup_logging
    from emp_packagex3.settings import load_settings

    settings = load_settings()
    log_dir = Path(settings.log_dir) if settings.log_dir.strip() else None
    setup_logging(debug=debug or settings.debug_logging, log_dir=log_dir)

    # Windowed EXE has no console: unhandled exceptions must reach the log
    # and trigger the feedback offer instead of vanishing silently.
    from emp_packagex3.crash_hook import install_crash_hook

    install_crash_hook()

    from emp_packagex3.app import run_app

    # Explorer "Open with" passes the document path as argv[1] – open it.
    initial_file = Path(positional[0]) if positional else None

    return run_app(initial_file=initial_file)


if __name__ == "__main__":
    raise SystemExit(main())
