"""App-level helper regressions (review stage 5)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_package_dir_for_file_variants(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from emp_packagex3.app import package_dir_for_file

    pkg = tmp_path / "Demo_1.0"
    (pkg / "Install").mkdir(parents=True)
    (pkg / "Files").mkdir(parents=True)
    (pkg / "Install" / "Setup.inf").write_text("[Setup]\r\n", encoding="utf-8")

    # Canonical: Install\Setup.inf -> package root
    assert package_dir_for_file(pkg / "Install" / "Setup.inf") == pkg
    # Any file below Install -> package root (was: ...\Install)
    (pkg / "Install" / "install.cmd").write_text("echo hi\r\n", encoding="utf-8")
    assert package_dir_for_file(pkg / "Install" / "install.cmd") == pkg
    # File in Files\ -> package root
    (pkg / "Files" / "setup.exe").write_bytes(b"MZ")
    assert package_dir_for_file(pkg / "Files" / "setup.exe") == pkg
    # Unrelated file -> parent dir fallback
    lonely = tmp_path / "loose.inf"
    lonely.write_text("[A]\r\n", encoding="utf-8")
    assert package_dir_for_file(lonely) == tmp_path


def test_main_help_and_unknown_args(capsys: object) -> None:
    from emp_packagex3.__main__ import main

    assert main(["--version"]) == 0
    assert main(["--help"]) == 0
    assert main(["--nonsense"]) == 2


def test_split_cli_args_for_file_association() -> None:
    from emp_packagex3.__main__ import split_cli_args

    # Explorer "Open with" passes the document path as positional argument
    positional, unknown = split_cli_args([r"C:\Paket\Install\Setup.inf"])
    assert positional == [r"C:\Paket\Install\Setup.inf"]
    assert unknown == []
    # known flags are neither positional nor unknown
    positional, unknown = split_cli_args(["--debug", r"D:\x.inf"])
    assert positional == [r"D:\x.inf"]
    assert unknown == []
    # genuinely unknown flags still surface
    positional, unknown = split_cli_args(["--nonsense", "a.inf"])
    assert positional == ["a.inf"]
    assert unknown == ["--nonsense"]


def test_main_window_loads_file_at_startup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    class _StubBoxes:
        # No modal QMessageBox in tests – a real warning dialog would block CI.
        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.app.QMessageBox", _StubBoxes)

    inf = tmp_path / "Setup.inf"
    inf.write_bytes(b"[SetupInfo]\r\nProductName=Demo\r\n")
    window = MainWindow()
    window.load_file_at_startup(inf)
    assert window._path == inf  # noqa: SLF001
    assert "Demo" in window._editor.toPlainText()  # noqa: SLF001

    # Missing file -> warning path (stubbed), editor untouched
    window._path = None  # noqa: SLF001
    window.load_file_at_startup(tmp_path / "missing.inf")
    assert window._path is None  # noqa: SLF001


def _stub_encoding_dialog(monkeypatch: pytest.MonkeyPatch, *, accept: bool) -> None:
    """Replace the encoding dialog: no modal window, deterministic choice."""
    from empirum_core.parser.encoding import DetectedEncoding

    class _StubDialog:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self._choice = DetectedEncoding(name="utf-8", has_bom=False, ambiguous=False)

        def exec(self) -> int:
            return 1 if accept else 0

        def chosen(self) -> DetectedEncoding:
            return self._choice

    monkeypatch.setattr("emp_packagex3.ui.encoding_dialog.EncodingChoiceDialog", _StubDialog)


def _ambiguous_inf(tmp_path: Path) -> Path:
    """UTF-8 with a multi-byte char and no BOM -> the detector stays ambiguous."""
    inf = tmp_path / "Setup.inf"
    inf.write_bytes("[SetupInfo]\r\nProductName=Café\r\n".encode())
    return inf


def test_encoding_choice_marks_document_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The encoding choice changes the next write -> unsaved state."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow
    from empirum_core.parser.encoding import detect_encoding

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_encoding_dialog(monkeypatch, accept=True)

    window = MainWindow()
    inf = _ambiguous_inf(tmp_path)
    assert detect_encoding(inf.read_bytes()).ambiguous is True  # precondition
    window.load_file_at_startup(inf)
    # set_encoding() clears the ambiguity flag again – the chosen encoding is
    # now fixed, the editor is writable and the choice counts as a change.
    assert window._editor.isReadOnly() is False  # noqa: SLF001
    assert window._dirty is True  # noqa: SLF001
    assert window.isWindowModified() is True


def test_encoding_choice_cancel_keeps_document_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cancelling stays read-only (R-02) and must not fake a modification."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app
    _stub_encoding_dialog(monkeypatch, accept=False)

    window = MainWindow()
    window.load_file_at_startup(_ambiguous_inf(tmp_path))
    assert window._editor.isReadOnly() is True  # noqa: SLF001
    assert window._dirty is False  # noqa: SLF001


def test_depot_sync_deferred_and_skips_unc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R-3: construction must not sync the depot; UNC shares are skipped."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    import empirum_services.local_depot as local_depot
    from emp_packagex3 import app as app_mod
    from emp_packagex3.app import MainWindow, _is_local_path
    from emp_packagex3.settings import AppSettings

    app = QApplication.instance() or QApplication([])
    _ = app

    assert _is_local_path(Path(r"C:\Depot")) is True
    assert _is_local_path(Path(r"\\srv\Store$\Depot")) is False

    calls: list[Path] = []

    def _fake_ensure(depot_dir: Path, **kwargs: object) -> Path:
        calls.append(Path(depot_dir))
        return Path(depot_dir) / "VERSION.json"

    monkeypatch.setattr(local_depot, "ensure_local_depot", _fake_ensure)

    settings = AppSettings()
    settings.depot_path = str(tmp_path / "depot")
    monkeypatch.setattr(app_mod, "load_settings", lambda *a, **k: settings)

    window = MainWindow()
    assert calls == []  # R-3: no blocking depot sync while constructing
    window.show()  # first paint
    assert calls == []  # ... and still nothing before the event loop runs
    QApplication.processEvents()  # flush the deferred singleShot(0)
    assert calls == [tmp_path / "depot"]
    window.hide()

    # Network depot: never touched from the UI thread (SMB may hang)
    settings.depot_path = r"\\srv\Store$\depot"
    window._ensure_local_depot()  # noqa: SLF001
    assert calls == [tmp_path / "depot"]


def test_pending_edit_survives_close(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A keystroke inside the debounce window must not be lost on close (R-1)."""
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWidgets import QMessageBox as _RealBoxes

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    asked: list[str] = []

    class _StubBoxes:
        StandardButton = _RealBoxes.StandardButton

        @staticmethod
        def question(*args: object, **kwargs: object) -> _RealBoxes.StandardButton:
            asked.append("question")
            return _RealBoxes.StandardButton.Discard

        @staticmethod
        def information(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.app.QMessageBox", _StubBoxes)

    inf = tmp_path / "Setup.inf"
    inf.write_bytes(b"[SetupInfo]\r\nProductName=Demo\r\n")
    window = MainWindow()
    window.load_file_at_startup(inf)
    assert window._dirty is False  # noqa: SLF001
    assert not window.isWindowModified()

    # Keystroke: the debounced sync/lint has not run yet -> _dirty is still False.
    window._editor.setPlainText("[SetupInfo]\r\nProductName=Demo2\r\n")  # noqa: SLF001
    assert window._dirty is False  # noqa: SLF001

    # Closing flushes the pending edit and therefore asks about unsaved changes.
    event = QCloseEvent()
    window.closeEvent(event)
    assert asked == ["question"]
    assert event.isAccepted()
    assert window._dirty is True  # noqa: SLF001
    assert window.isWindowModified()


def test_noop_flush_keeps_document_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-3: a flush without an edit must not fake unsaved changes (``*``)."""
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QTextCursor
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.app import MainWindow

    app = QApplication.instance() or QApplication([])
    _ = app

    class _StubBoxes:
        @staticmethod
        def information(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def warning(*args: object, **kwargs: object) -> None:
            return None

        @staticmethod
        def critical(*args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr("emp_packagex3.app.QMessageBox", _StubBoxes)

    inf = tmp_path / "Setup.inf"
    inf.write_bytes(b"[SetupInfo]\r\nProductName=Demo\r\n")
    window = MainWindow()
    window.load_file_at_startup(inf)
    assert window._dirty is False

    window.run_lint()  # flushes the editor text without any edit
    assert window._dirty is False
    assert not window.isWindowModified()

    # A real edit is still tracked – even when still inside the debounce window.
    window._editor.moveCursor(QTextCursor.MoveOperation.End)
    window._editor.insertPlainText("[Set:Extra]\r\nEcho hi\r\n")
    assert window._dirty is False  # debounce pending
    window._flush_pending_edit()
    assert window._dirty is True
    assert window.isWindowModified()

