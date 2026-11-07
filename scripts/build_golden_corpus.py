"""Build golden Setup.inf corpus with explicit encodings and CRLF."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "testdata" / "golden"


SAMPLES: list[tuple[str, str, str]] = [
    (
        "01_minimal.inf",
        "cp1252",
        "; Golden 01 – minimal\r\n"
        "[SetupInfo]\r\n"
        "ProductName=Demo Product\r\n"
        "ProductVersion=1.0.0\r\n"
        "Manufacturer=Hodrius Systems\r\n"
        "\r\n"
        "[Application]\r\n"
        "AppType=MSI\r\n"
        "CallTimeOut=3600000\r\n"
        "\r\n"
        "[Product]\r\n"
        "Platform=x64\r\n"
        "; Branding\r\n"
        "Icon=Setup.ico\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Installing Demo Product\r\n"
        "Run=%Src%\\Files\\Demo.msi\r\n",
    ),
    (
        "02_umlauts.inf",
        "cp1252",
        "; Golden 02 – Umlauts CP1252\r\n"
        "[SetupInfo]\r\n"
        'ProductName="Büro Suite ÄÖÜ"\r\n'
        "ProductVersion=2.1.0\r\n"
        'Manufacturer="Müller & Söhne GmbH"\r\n'
        "\r\n"
        "[Application]\r\n"
        "AppType=EXE\r\n"
        "\r\n"
        "[Product]\r\n"
        "Platform=x64\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Installation der Büro Suite\r\n"
        "; Path with spaces\r\n"
        'Run="%Src%\\Files\\Setup.exe" /S\r\n'
        "DelTree=%Dst%\\Büro\r\n",
    ),
    (
        "03_shell_and_uninstall.inf",
        "cp1252",
        "; Golden 03 – shell + uninstall prefixes\r\n"
        "[SetupInfo]\r\n"
        "ProductName=ShellLinks Demo\r\n"
        "ProductVersion=0.9.0\r\n"
        "\r\n"
        "[Product]\r\n"
        "#Shell:CreateLinks\r\n"
        "\r\n"
        "[CreateLinks]\r\n"
        "LinkName=Demo\r\n"
        "LinkPath=%Dst%\\Demo.exe\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Step one\r\n"
        "Echo=Step two\r\n"
        "\r\n"
        "[Set_Uninstall]\r\n"
        "Echo=Removing Demo\r\n"
        "--Echo=Uninstall branch\r\n",
    ),
    (
        "04_registry_block.inf",
        "cp1252",
        "; Golden 04 – registry-like keys\r\n"
        "[SetupInfo]\r\n"
        "ProductName=Reg Demo\r\n"
        "\r\n"
        "[Set_Registry]\r\n"
        "Root=HKLM\r\n"
        "Key=Software\\Hodrius\\Demo\r\n"
        "ValueName=Installed\r\n"
        "ValueData=1\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Writing registry\r\n"
        "#Set_Registry\r\n",
    ),
    (
        "05_blank_and_preamble.inf",
        "cp1252",
        "; preamble comment before sections\r\n"
        "\r\n"
        "[SetupInfo]\r\n"
        "ProductName=Preamble Demo\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Go\r\n"
        "\r\n"
        "\r\n"
        "[Set_Uninstall]\r\n"
        "Echo=Gone\r\n",
    ),
    (
        "06_variables.inf",
        "cp1252",
        "[SetupInfo]\r\n"
        "ProductName=Var Demo\r\n"
        "\r\n"
        "[Application]\r\n"
        "Src=%PackageDir%\r\n"
        "Dst=%ProgramFilesDir%\\Demo\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=%ProductName%\r\n"
        "Run=%Src%\\setup.exe\r\n",
    ),
    (
        "07_quoted_paths.inf",
        "cp1252",
        "[SetupInfo]\r\n"
        "ProductName=Quotes\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        'Copy="%Src%\\Files\\A B\\tool.exe","%Dst%\\tool.exe"\r\n'
        'Echo="Hello; world"\r\n',
    ),
    (
        "08_utf8_bom.inf",
        "utf-8-sig",
        "; Golden 08 – UTF-8 BOM\r\n"
        "[SetupInfo]\r\n"
        "ProductName=UTF8 Café\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=Café install\r\n",
    ),
    (
        "09_many_sections.inf",
        "cp1252",
        "[SetupInfo]\r\n"
        "ProductName=Many\r\n"
        "\r\n"
        "[Application]\r\n"
        "AppType=Script\r\n"
        "\r\n"
        "[Product]\r\n"
        "Platform=x64\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=A\r\n"
        "\r\n"
        "[Set_Uninstall]\r\n"
        "Echo=B\r\n"
        "\r\n"
        "[Custom_Checks]\r\n"
        "Echo=C\r\n"
        "\r\n"
        "[Error_Install]\r\n"
        "Echo=fail\r\n"
        "\r\n"
        "[-Error_Uninstall]\r\n"
        "--Echo=fail uninstall\r\n",
    ),
    (
        "10_unknown_raw.inf",
        "cp1252",
        "[SetupInfo]\r\n"
        "ProductName=Raw\r\n"
        "\r\n"
        "[Set_Install]\r\n"
        "Echo=start\r\n"
        "!!! not a normal key line !!!\r\n"
        "   indented raw\r\n"
        "=weird\r\n"
        "Echo=end\r\n",
    ),
]

# Expand to 25 files with small variants (Phase-1 corpus target)
for i in range(11, 26):
    SAMPLES.append(
        (
            f"{i:02d}_variant.inf",
            "cp1252",
            f"; Golden {i:02d} variant\r\n"
            f"[SetupInfo]\r\n"
            f"ProductName=Variant{i}\r\n"
            f"ProductVersion=1.0.{i}\r\n"
            f"\r\n"
            f"[Application]\r\n"
            f"Reboot=0\r\n"
            f"\r\n"
            f"[Set_Install]\r\n"
            f"Echo=Variant {i}\r\n"
            f"Run=%Src%\\Files\\v{i}.exe\r\n"
            f"If=%ErrorLevel%\r\n"
            f"\r\n"
            f"[Set_Uninstall]\r\n"
            f"Echo=Remove {i}\r\n"
            f"DelTree=%Dst%\\V{i}\r\n",
        )
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, encoding, text in SAMPLES:
        path = OUT / name
        if encoding == "utf-8-sig":
            path.write_bytes(text.encode("utf-8-sig"))
        else:
            path.write_bytes(text.encode(encoding))
        print(f"wrote {path.name} ({encoding}, {path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
