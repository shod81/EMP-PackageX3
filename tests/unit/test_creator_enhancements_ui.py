from __future__ import annotations

from pathlib import Path

import pytest

from empirum_core.inspect import FolderCopySpec, RegFileSpec


def test_dialogs_specs_and_wizard_enhancements_page(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from emp_packagex3.wizard.creator import (
        AddFolderDialog,
        AddRegistryValueDialog,
        AddShellLinkDialog,
        CreatorWizard,
        RegImportDialog,
    )

    app = QApplication.instance() or QApplication([])
    _ = app

    # 1. AddFolderDialog
    test_dir = tmp_path / "SubConfig"
    test_dir.mkdir()
    dlg_f = AddFolderDialog(initial_dir=str(test_dir))
    assert dlg_f._folder_name.text() == "SubConfig"
    # Select preset ProgramFiles with subfolder
    dlg_f._target_path.setCurrentIndex(0)
    spec_f = dlg_f.get_spec()
    assert spec_f.folder_name == "SubConfig"
    assert "SubConfig" in spec_f.target_path
    assert spec_f.xcopy_flags == "/S /H /E /V /Y"
    assert spec_f.delete_on_uninstall is True

    # 2. AddRegistryValueDialog
    dlg_r = AddRegistryValueDialog()
    dlg_r._root.setCurrentText("HKCU")
    dlg_r._key_path.setText(r"Software\TestApp")
    dlg_r._value_name.setText("Settings")
    dlg_r._type.setCurrentText("REG_SZ")
    dlg_r._value_data.setText("Active")
    dlg_r._delete_on_uninstall.setChecked(True)
    spec_r = dlg_r.get_spec()
    assert spec_r.root == "HKCU"
    assert spec_r.key_path == r"Software\TestApp"
    assert spec_r.value_name == "Settings"
    assert spec_r.value_data == "Active"
    assert spec_r.delete_on_uninstall is True

    # 3. RegImportDialog
    reg_file = tmp_path / "app.reg"
    reg_file.write_text(
        "Windows Registry Editor Version 5.00\n\n"
        "[HKEY_CURRENT_USER\\Software\\Test]\n\"A\"=\"1\"\n",
        encoding="utf-8",
    )
    dlg_reg = RegImportDialog(str(reg_file))
    assert dlg_reg.has_hkcu() is True
    assert dlg_reg.import_mode() == "reg_exe"
    dlg_reg._mode_convert.setChecked(True)
    assert dlg_reg.import_mode() == "convert"

    # 4. AddShellLinkDialog
    dlg_s = AddShellLinkDialog(product_name="MyApp", vendor="MyVendor")
    assert dlg_s._name.text() == "MyApp"
    assert dlg_s._subfolder.text() == "MyVendor"
    dlg_s._target.setText(r"%App%\MyApp.exe")
    # Default destination is the All Users start menu (%CommonPrograms%)
    assert dlg_s._dest.currentData() == "common_programs"
    assert dlg_s._subfolder.isEnabled()
    spec_s = dlg_s.get_spec()
    assert spec_s.name == "MyApp"
    assert spec_s.subfolder == "MyVendor"
    assert spec_s.destination == "common_programs"
    assert spec_s.target == r"%App%\MyApp.exe"

    # Switching to CommonDesktop disables the start-menu subfolder
    dlg_s._dest.setCurrentIndex(1)
    assert dlg_s._dest.currentData() == "common_desktop"
    assert not dlg_s._subfolder.isEnabled()
    spec_desk = dlg_s.get_spec()
    assert spec_desk.destination == "common_desktop"
    assert spec_desk.subfolder == ""

    # 5. CreatorWizard integration
    wiz = CreatorWizard(theme="dark")
    assert wiz._stack.count() == 7

    # Add items to wizard
    wiz._folder_copies.append(
        FolderCopySpec(
            folder_name="Plugins",
            target_path=r"%ProgramFiles%\MyApp\Plugins",
            xcopy_flags="/S /H /E /V /Y",
            delete_on_uninstall=True,
        )
    )
    wiz._refresh_folder_table()
    assert wiz._table_folders.rowCount() == 1

    wiz._reg_files.append(
        RegFileSpec(
            file_name="app.reg",
            local_source_path=str(reg_file),
            import_mode="reg_exe",
        )
    )
    wiz._registry_entries.append(spec_r)
    wiz._refresh_registry_table()
    assert wiz._table_registry.rowCount() == 2

    wiz._shell_links.append(spec_s)
    wiz._shell_links.append(spec_desk)
    wiz._refresh_shell_table()
    assert wiz._table_shell_links.rowCount() == 2
    # Table shows the real destination path per link
    assert "%CommonPrograms%" in wiz._table_shell_links.item(0, 1).text()
    assert "%CommonDesktop%" in wiz._table_shell_links.item(1, 1).text()

    # Verify _collect returns them in metadata
    wiz._name.setText("MyApp")
    wiz._vendor.setText("MyVendor")
    wiz._version.setText("1.0")
    wiz._collect()
    meta = wiz._meta
    assert len(meta.folder_copies) == 1
    assert meta.folder_copies[0].folder_name == "Plugins"
    assert len(meta.reg_files) == 1
    assert meta.reg_files[0].file_name == "app.reg"
    assert len(meta.registry_entries) == 1
    assert meta.registry_entries[0].root == "HKCU"
    assert len(meta.shell_links) == 2
    assert meta.shell_links[0].name == "MyApp"
    assert meta.shell_links[0].destination == "common_programs"
    assert meta.shell_links[1].destination == "common_desktop"

    # Verify summary page reflects them
    wiz._refresh_summary()
    summary_text = wiz._summary.toPlainText()
    assert "Ordnerkopien     : 1 Verzeichnisse" in summary_text
    assert "Registry-Einträge: 2 Einträge" in summary_text
    assert "Startmenü-Icons  : 2 Verknüpfungen" in summary_text

    # Test removals
    wiz._table_folders.setCurrentCell(0, 0)
    wiz._remove_folder_entry()
    assert len(wiz._folder_copies) == 0
    assert wiz._table_folders.rowCount() == 0

    wiz._table_registry.setCurrentCell(0, 0)
    wiz._remove_registry_entry()
    assert len(wiz._reg_files) == 0
    assert wiz._table_registry.rowCount() == 1

    wiz._table_registry.setCurrentCell(0, 0)
    wiz._remove_registry_entry()
    assert len(wiz._registry_entries) == 0
    assert wiz._table_registry.rowCount() == 0

    wiz._table_shell_links.setCurrentCell(0, 0)
    wiz._remove_shell_link_entry()
    assert len(wiz._shell_links) == 1
    wiz._table_shell_links.setCurrentCell(0, 0)
    wiz._remove_shell_link_entry()
    assert len(wiz._shell_links) == 0
    assert wiz._table_shell_links.rowCount() == 0
