from __future__ import annotations

from pathlib import Path

from empirum_core.inspect import (
    FolderCopySpec,
    PackageMetadata,
    RegFileSpec,
    RegistryEntrySpec,
    ShellLinkSpec,
)
from empirum_core.linter import lint_document
from empirum_core.serializer import serialize_document
from empirum_core.templates import render_template
from empirum_services.creator.generator import generate_package


def test_template_folder_copies_and_deltree() -> None:
    meta = PackageMetadata(
        product_name="FolderApp",
        product_version="1.0.0",
        manufacturer="Acme",
        package_type="Script",
        folder_copies=[
            FolderCopySpec(
                folder_name="ConfigDir",
                target_path=r"%ProgramFiles%\FolderApp\Config",
                xcopy_flags="/S /H /E /V /Y",
                delete_on_uninstall=True,
            ),
            FolderCopySpec(
                folder_name="DataDir",
                target_path=r"%CommonAppdata%\FolderApp\Data",
                xcopy_flags="/S /E /Y",
                delete_on_uninstall=False,
            ),
        ],
    )
    doc = render_template("script", meta)
    inf_text = serialize_document(doc)

    # Check xcopy commands
    expected_xcopy_1 = (
        'CallHidden cmd.exe /c xcopy "%Src%\\Files\\ConfigDir" '
        '"%ProgramFiles%\\FolderApp\\Config" /S /H /E /V /Y'
    )
    expected_xcopy_2 = (
        'CallHidden cmd.exe /c xcopy "%Src%\\Files\\DataDir" '
        '"%CommonAppdata%\\FolderApp\\Data" /S /E /Y'
    )
    assert expected_xcopy_1 in inf_text
    assert expected_xcopy_2 in inf_text

    # Check uninstall DelTree
    assert '-DelTree "%ProgramFiles%\\FolderApp\\Config"' in inf_text
    assert '-DelTree "%CommonAppdata%\\FolderApp\\Data"' not in inf_text


def test_template_reg_file_import_and_hkcu_auto_aw() -> None:
    meta = PackageMetadata(
        product_name="RegApp",
        product_version="2.0",
        manufacturer="Acme",
        package_type="EXE",
        reg_files=[
            RegFileSpec(
                file_name="settings.reg",
                import_mode="reg_exe",
                target_subfolder="Reg",
            ),
        ],
        registry_entries=[
            RegistryEntrySpec(
                root="HKCU",
                key_path=r"Software\Acme\RegApp",
                value_name="UserKey",
                reg_type="REG_SZ",
                value_data="Value1",
                delete_on_uninstall=True,
            ),
            RegistryEntrySpec(
                root="HKLM",
                key_path=r"Software\Acme\RegApp",
                value_name="SystemKey",
                reg_type="REG_DWORD",
                value_data="1",
                delete_on_uninstall=False,
            ),
        ],
    )
    doc = render_template("exe", meta)
    inf_text = serialize_document(doc)

    # Check reg import call
    expected_reg_call = (
        'CallHidden cmd.exe /c reg.exe import "%Src%\\Files\\Reg\\settings.reg"'
    )
    assert expected_reg_call in inf_text

    # Check [Reg:Product] section
    sec_reg = doc.section("Reg:Product")
    assert sec_reg is not None
    reg_lines = [getattr(n, "text", "") for n in sec_reg.lines]
    exp_hkcu = '-HKCU,"Software\\Acme\\RegApp","UserKey",0x00000000,"Value1"'
    exp_hklm = 'HKLM,"Software\\Acme\\RegApp","SystemKey",0x00010001,1'
    assert any(exp_hkcu in line for line in reg_lines)
    assert any(exp_hklm in line for line in reg_lines)

    # Check automatic /AW flag in Application header
    app_sec = doc.section("Application")
    assert app_sec is not None
    app_text = serialize_document(doc)
    assert "/AW" in app_text


def test_template_shell_links() -> None:
    meta = PackageMetadata(
        product_name="IconApp",
        product_version="1.0",
        manufacturer="Acme",
        package_type="MSI",
        shell_links=[
            ShellLinkSpec(
                name="IconApp Start",
                subfolder="Acme Tools",
                target=r"%ProgramFiles%\Acme\app.exe",
                arguments="--silent",
                working_dir=r"%ProgramFiles%\Acme",
            ),
            ShellLinkSpec(
                name="IconApp Minimal",
                subfolder="",
                target=r"%ProgramFiles%\Acme\app.exe",
            ),
        ],
    )
    doc = render_template("msi", meta)

    sec_shell = doc.section("Shell:Product")
    assert sec_shell is not None
    shell_lines = [getattr(n, "text", "") for n in sec_shell.lines]

    expected_link_1 = (
        r'"%CommonPrograms%\Acme Tools\IconApp Start", "%ProgramFiles%\Acme\app.exe", '
        r'"--silent", "%ProgramFiles%\Acme"'
    )
    expected_link_2 = (
        r'"%CommonPrograms%\IconApp Minimal", "%ProgramFiles%\Acme\app.exe"'
    )
    assert any(expected_link_1 in line for line in shell_lines)
    assert any(expected_link_2 in line for line in shell_lines)


def test_template_shell_link_common_desktop() -> None:
    meta = PackageMetadata(
        product_name="DeskApp",
        product_version="1.0",
        manufacturer="Acme",
        package_type="MSI",
        shell_links=[
            ShellLinkSpec(
                destination="common_desktop",
                name="DeskApp",
                # Subfolder is a Start-menu concept and must not leak into
                # the CommonDesktop path.
                subfolder="Acme Tools",
                target=r"%ProgramFiles%\Acme\desk.exe",
            ),
            ShellLinkSpec(
                name="DeskApp Menu",
                subfolder="Acme Tools",
                target=r"%ProgramFiles%\Acme\desk.exe",
            ),
        ],
    )
    doc = render_template("msi", meta)

    sec_shell = doc.section("Shell:Product")
    assert sec_shell is not None
    shell_lines = [getattr(n, "text", "") for n in sec_shell.lines]
    expected_desktop = r'"%CommonDesktop%\DeskApp", "%ProgramFiles%\Acme\desk.exe"'
    expected_programs = (
        r'"%CommonPrograms%\Acme Tools\DeskApp Menu", "%ProgramFiles%\Acme\desk.exe"'
    )
    assert any(expected_desktop in line for line in shell_lines)
    assert any(expected_programs in line for line in shell_lines)
    # Desktop links never carry a subfolder
    assert not any(r"%CommonDesktop%\Acme Tools" in line for line in shell_lines)


def test_all_templates_lint_clean_with_all_enhancements() -> None:
    meta = PackageMetadata(
        product_name="SuperApp",
        product_version="3.0",
        manufacturer="AcmeCorp",
        folder_copies=[
            FolderCopySpec(
                folder_name="Extra",
                target_path=r"%ProgramFiles%\Extra",
                xcopy_flags="/S /H /E /V /Y",
                delete_on_uninstall=True,
            )
        ],
        reg_files=[
            RegFileSpec(file_name="extra.reg", import_mode="reg_exe")
        ],
        registry_entries=[
            RegistryEntrySpec(
                root="HKLM",
                key_path=r"Software\Extra",
                value_name="Mode",
                reg_type="REG_SZ",
                value_data="Auto",
            )
        ],
        shell_links=[
            ShellLinkSpec(
                name="Extra App",
                subfolder="ExtraSuite",
                target=r"%ProgramFiles%\Extra\extra.exe",
            )
        ],
    )
    for kind in ("msi", "exe", "script", "links"):
        meta.package_type = kind.upper()
        doc = render_template(kind, meta)
        diags = lint_document(doc)
        errors = [d for d in diags if d.severity.value == "error"]
        assert errors == [], f"{kind} errors: {[e.message for e in errors]}"


def test_generate_package_with_folder_and_reg_copy(tmp_path: Path) -> None:
    # Prepare source directory and .reg file
    source_dir = tmp_path / "source_folder"
    source_dir.mkdir()
    (source_dir / "sample.txt").write_text("Hello World", encoding="utf-8")

    source_reg = tmp_path / "custom.reg"
    source_reg.write_text(
        "Windows Registry Editor Version 5.00\n\n"
        "[HKEY_LOCAL_MACHINE\\Software\\TestPkg]\n"
        "\"TestVal\"=\"Value\"\n",
        encoding="utf-8",
    )

    dest_dir = tmp_path / "packages"
    meta = PackageMetadata(
        product_name="TestPkg",
        product_version="1.0",
        manufacturer="Vendor",
        package_type="Script",
        folder_copies=[
            FolderCopySpec(
                folder_name="MyData",
                target_path=r"%ProgramFiles%\TestPkg\Data",
                local_source_path=str(source_dir),
                delete_on_uninstall=True,
            )
        ],
        reg_files=[
            RegFileSpec(
                file_name="custom.reg",
                local_source_path=str(source_reg),
                import_mode="reg_exe",
            )
        ],
    )

    result = generate_package(meta, dest_dir, kind="Script", copy_source=False)
    assert result.setup_inf.is_file()

    # Check physical folder was copied to Files/MyData
    copied_folder = result.package_dir / "Files" / "MyData"
    assert copied_folder.is_dir()
    assert (copied_folder / "sample.txt").read_text(encoding="utf-8") == "Hello World"

    # Check physical reg file was copied to Files/Reg/custom.reg
    copied_reg = result.package_dir / "Files" / "Reg" / "custom.reg"
    assert copied_reg.is_file()
    assert "TestPkg" in copied_reg.read_text(encoding="utf-8")

    # Check Setup.inf contents
    inf_content = result.setup_inf.read_text(encoding="cp1252")
    assert 'xcopy "%Src%\\Files\\MyData"' in inf_content
    assert 'reg.exe import "%Src%\\Files\\Reg\\custom.reg"' in inf_content
    assert '-DelTree "%ProgramFiles%\\TestPkg\\Data"' in inf_content


def test_generate_package_with_convert_reg(tmp_path: Path) -> None:
    source_reg = tmp_path / "convert_me.reg"
    source_reg.write_text(
        "Windows Registry Editor Version 5.00\n\n"
        "[HKEY_LOCAL_MACHINE\\Software\\ConvertedApp]\n"
        "\"ConvertedKey\"=\"Worked\"\n",
        encoding="utf-8",
    )

    dest_dir = tmp_path / "packages_converted"
    meta = PackageMetadata(
        product_name="ConvertedApp",
        product_version="1.0",
        manufacturer="Vendor",
        package_type="Script",
        reg_files=[
            RegFileSpec(
                file_name="convert_me.reg",
                local_source_path=str(source_reg),
                import_mode="convert",
            )
        ],
    )

    result = generate_package(meta, dest_dir, kind="Script", copy_source=False)
    assert result.setup_inf.is_file()

    # Mode 'convert' should NOT place the file into Files/Reg
    copied_reg = result.package_dir / "Files" / "Reg" / "convert_me.reg"
    assert not copied_reg.exists()

    # But it should be present in [Reg:Product] in Setup.inf
    inf_content = result.setup_inf.read_text(encoding="cp1252")
    assert "ConvertedKey" in inf_content
    assert 'HKLM,"Software\\ConvertedApp","ConvertedKey",0x00000000,"Worked"' in inf_content
