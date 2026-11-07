"""Application icon resources."""

from __future__ import annotations

from emp_packagex3.icons import icon_path, load_app_icon


def test_icon_files_exist() -> None:
    ico = icon_path("emp_packagex3.ico")
    png = icon_path("emp_packagex3.png")
    assert ico is not None and ico.is_file()
    assert png is not None and png.is_file()
    assert ico.stat().st_size > 1000
    assert png.stat().st_size > 1000


def test_load_app_icon_non_null() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    _ = app
    icon = load_app_icon()
    assert not icon.isNull()
