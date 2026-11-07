"""Dialog: Empirum PackageStore deploy."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from emp_packagex3.ui.tooltip_mode import apply_tooltip_mode, bind_field
from empirum_services.package_readiness import ReadinessLevel, check_package_readiness
from empirum_services.package_store import (
    DeployMode,
    PackageStoreError,
    deploy_to_package_store,
    expand_empirum_path,
)


class PackageStoreDeployDialog(QDialog):
    def __init__(
        self,
        *,
        package_dir: Path | None,
        store_root: str,
        empirum_server: str = "",
        manufacturer: str = "",
        product: str = "",
        version: str = "",
        default_mode: str = "vendor_product_version",
        tooltip_mode: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nach Empirum PackageStore deployen")
        self.resize(680, 520)
        self._package = QLineEdit(str(package_dir) if package_dir else "")
        self._store = QLineEdit(store_root)
        self._server = QLineEdit(empirum_server)
        self._mfr = QLineEdit(manufacturer)
        self._product = QLineEdit(product)
        self._version = QLineEdit(version)
        self._mode = QComboBox()
        self._mode.addItem("Hersteller / Produkt / Version", DeployMode.VENDOR_PRODUCT_VERSION)
        self._mode.addItem("Flach (Produkt_Version)", DeployMode.FLAT)
        if default_mode == DeployMode.FLAT.value:
            self._mode.setCurrentIndex(1)
        self._overwrite = QCheckBox("Vorhandenes Ziel überschreiben")
        self._dry = QCheckBox("Nur prüfen (Dry-Run)")
        self._dry.setChecked(True)
        # Target signature of the last successful dry-run in this dialog session
        self._verified_target: str | None = None
        self._log = QTextEdit()
        self._log.setReadOnly(True)

        browse = QPushButton("…")
        browse.clicked.connect(self._browse_package)
        pkg_row = QHBoxLayout()
        pkg_row.addWidget(self._package)
        pkg_row.addWidget(browse)

        check_btn = QPushButton("Paket prüfen")
        check_btn.clicked.connect(self._run_readiness)
        bind_field(check_btn, "store.check")

        self._repair_btn = QPushButton("Fehlende Standardsektionen ergänzen…")
        self._repair_btn.setVisible(False)
        self._repair_btn.clicked.connect(self._run_skeleton_repair)
        bind_field(self._repair_btn, "store.repair")

        bind_field(self._package, "store.package")
        bind_field(browse, "store.browse")
        bind_field(self._server, "store.server")
        bind_field(self._store, "store.root")
        bind_field(self._mfr, "store.mfr")
        bind_field(self._product, "store.product")
        bind_field(self._version, "store.version")
        bind_field(self._mode, "store.mode")
        bind_field(self._overwrite, "store.overwrite")
        bind_field(self._dry, "store.dry")
        bind_field(self._log, "store.log")

        form = QFormLayout()
        form.addRow("Paketordner", pkg_row)
        form.addRow("EmpirumServer (optional)", self._server)
        form.addRow("PackageStore-Root", self._store)
        form.addRow("Hersteller", self._mfr)
        form.addRow("Produkt", self._product)
        form.addRow("Version", self._version)
        form.addRow("Zielstruktur", self._mode)
        form.addRow(self._overwrite)
        form.addRow(self._dry)

        hint = QLabel(
            "Vor dem Deploy: „Paket prüfen“ (Struktur + Lint).\n"
            "Kopiert Install\\Setup.inf + Files nach Configurator$\\PackageStore.\n"
            "Import in ein Software-Register danach manuell in der Empirum MMC."
        )
        hint.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Deploy")
        buttons.accepted.connect(self._run)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addWidget(hint)
        root.addLayout(form)
        root.addWidget(check_btn)
        root.addWidget(self._repair_btn)
        root.addWidget(self._log)
        root.addWidget(buttons)
        apply_tooltip_mode(self, tooltip_mode)

    def _browse_package(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Empirum-Paketordner wählen")
        if path:
            self._package.setText(path)

    def _run_readiness(self) -> bool:
        pkg = self._package.text().strip()
        if not pkg:
            QMessageBox.warning(self, "PackageStore", "Bitte Paketordner wählen.")
            return False
        report = check_package_readiness(Path(pkg))
        self._log.clear()
        self._log.append("\n".join(report.summary_lines()))
        # Standard skeleton repair is offered whenever VAL-012 diagnostics exist.
        self._repair_btn.setVisible(
            any(d.code == "VAL-012" for d in report.diagnostics)
        )
        if report.level == ReadinessLevel.FAIL:
            QMessageBox.warning(
                self,
                "Paketprüfung fehlgeschlagen",
                "Kritische Probleme – Deploy blockiert.\nDetails im Protokoll.",
            )
            return False
        if report.level == ReadinessLevel.WARN:
            QMessageBox.information(
                self,
                "Paketprüfung mit Warnungen",
                "Deploy möglich, aber Warnungen beachten (/AW, Files\\, Lint).",
            )
        else:
            QMessageBox.information(self, "Paketprüfung OK", "Struktur und Lint ohne Fehler.")
        return True

    def _run_skeleton_repair(self) -> None:
        """Repair missing standard sections on disk (VAL-012 blocker)."""
        from empirum_services.package_readiness import repair_missing_standard_sections

        pkg = self._package.text().strip()
        if not pkg:
            QMessageBox.warning(self, "PackageStore", "Bitte Paketordner wählen.")
            return
        count = sum(
            1 for d in check_package_readiness(Path(pkg)).diagnostics
            if d.code == "VAL-012"
        )
        answer = QMessageBox.question(
            self,
            "Standardskelett ergänzen",
            f"{count} fehlende Standardsektion(en) ergänzen (Fehler-Handler mit "
            "kanonischem Abort-Block, sonst leere Stubs)\n"
            "und kanonische #Aufrufe in [Product] sichern?\n\n"
            "Es wird automatisch ein WAL-Backup der Setup.inf angelegt "
            "(außerhalb des Pakets, damit der Deploy sauber bleibt).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            result = repair_missing_standard_sections(Path(pkg))
        except (PackageStoreError, OSError) as exc:
            self._log.append(f"Reparatur fehlgeschlagen: {exc}")
            QMessageBox.critical(self, "PackageStore", f"Reparatur fehlgeschlagen:\n{exc}")
            return
        self._log.append(
            "Standardskelett ergänzt: "
            + (", ".join(f"[{s}]" for s in result.added_sections) or "(keine Sektionen)")
            + " · #Refs: "
            + (", ".join(result.added_refs) or "(keine)")
            + (f" · Backup: {result.backup_path}" if result.backup_path else "")
        )
        # Disk changed -> previous dry-run verification no longer applies.
        self._verified_target = None
        self._run_readiness()

    def _run(self) -> None:
        pkg = self._package.text().strip()
        store = self._store.text().strip()
        if not pkg or not store:
            QMessageBox.warning(self, "PackageStore", "Paket und PackageStore-Pfad nötig.")
            return
        report = check_package_readiness(Path(pkg))
        self._log.append("\n".join(report.summary_lines()))
        if not report.ok_to_deploy:
            QMessageBox.warning(
                self,
                "PackageStore",
                "Paketprüfung fehlgeschlagen – bitte Setup.inf/Struktur korrigieren.",
            )
            return
        if report.level == ReadinessLevel.WARN:
            answer = QMessageBox.question(
                self,
                "Warnungen vorhanden",
                "Paket hat Warnungen. Trotzdem fortfahren?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        mode = self._mode.currentData()
        assert isinstance(mode, DeployMode)
        signature = "|".join(
            (
                pkg,
                store,
                self._server.text().strip(),
                self._mfr.text().strip(),
                self._product.text().strip(),
                self._version.text().strip(),
                mode.value,
            )
        )
        if not self._dry.isChecked() and signature != self._verified_target:
            answer = QMessageBox.question(
                self,
                "Echtes Deploy",
                "Ohne vorherigen Dry-Run für dieses Ziel wirklich kopieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._dry.setChecked(True)
                return
        try:
            expanded = expand_empirum_path(
                store, empirum_server=self._server.text().strip()
            )
            self._log.append(f"Ziel-Root (expandiert): {expanded}")
            result = deploy_to_package_store(
                Path(pkg),
                store,
                manufacturer=self._mfr.text().strip(),
                product=self._product.text().strip(),
                version=self._version.text().strip(),
                mode=mode,
                overwrite=self._overwrite.isChecked(),
                empirum_server=self._server.text().strip(),
                dry_run=self._dry.isChecked(),
            )
        except PackageStoreError as exc:
            self._log.append(f"Fehler: {exc}")
            QMessageBox.warning(self, "PackageStore", str(exc))
            return
        except OSError as exc:
            self._log.append(f"OS-Fehler: {exc}")
            QMessageBox.critical(self, "PackageStore", str(exc))
            return
        self._log.append(result.message)
        if result.dry_run:
            # Keep the checkbox checked: the user consciously unchecks for the real run.
            self._verified_target = signature
            QMessageBox.information(
                self,
                "Dry-Run OK",
                result.message + "\n\nHaken entfernen und erneut Deploy für das echte Kopieren.",
            )
            return
        QMessageBox.information(self, "Deploy OK", result.message)
        self.accept()
