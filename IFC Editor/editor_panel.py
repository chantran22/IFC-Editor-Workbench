# -*- coding: utf-8 -*-
"""
IFC Code Editor — main dockable panel.

Layout:
  ┌─────────────────┬─────────────────────────────┐
  │  Snippet Browser│  Code Editor (top)          │
  │  (left dock)    │  Console / Output (bottom)  │
  └─────────────────┴─────────────────────────────┘

The FreeCAD 3D viewport lives separately — we don't embed it.
"""

import os
import sys
import glob
import traceback

# WB root = same folder as this file (editor_panel.py is at WB root level)
_WB_ROOT = os.path.dirname(os.path.abspath(__file__))
if _WB_ROOT not in sys.path:
    sys.path.insert(0, _WB_ROOT)

import FreeCAD
import FreeCADGui as Gui

from PySide2 import QtCore, QtGui, QtWidgets


# ---------------------------------------------------------------------------
# Syntax Highlighter — IFC-aware Python
# ---------------------------------------------------------------------------

class IFCSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Python highlighter with extra colours for ifcopenshell keywords."""

    def __init__(self, document):
        super().__init__(document)
        rules = []

        def rule(pattern, color, bold=False, italic=False):
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QColor(color))
            if bold:   fmt.setFontWeight(QtGui.QFont.Bold)
            if italic: fmt.setFontItalic(True)
            rules.append((QtCore.QRegExp(pattern), fmt))

        # Python keywords
        kw_color = "#CC7A00"
        for kw in ["and","as","assert","break","class","continue","def","del",
                   "elif","else","except","finally","for","from","global","if",
                   "import","in","is","lambda","not","or","pass","raise","return",
                   "try","while","with","yield","None","True","False"]:
            rule(f"\\b{kw}\\b", kw_color, bold=True)

        # ifcopenshell classes / entities
        ifc_color = "#2196F3"
        for cls in ["IfcWall","IfcColumn","IfcBeam","IfcSlab","IfcDoor","IfcWindow",
                    "IfcProject","IfcSite","IfcBuilding","IfcBuildingStorey",
                    "IfcProduct","IfcSpace","IfcOpeningElement","IfcStair",
                    "ifcopenshell","api","geom","util","model"]:
            rule(f"\\b{cls}\\b", ifc_color, bold=True)

        # api sub-modules
        for mod in ["root","geometry","spatial","material","pset","unit",
                    "owner","type","aggregate","style"]:
            rule(f"\\b{mod}\\b", "#00897B")

        # Strings
        rule('"[^"\\\\]*(\\\\.[^"\\\\]*)*"', "#43A047")
        rule("'[^'\\\\]*(\\\\.[^'\\\\]*)*'", "#43A047")

        # Comments
        rule("#[^\n]*", "#888888", italic=True)

        # Numbers
        rule("\\b[0-9]+\\.?[0-9]*\\b", "#AB47BC")

        # Decorators
        rule("@[A-Za-z_][A-Za-z0-9_]*", "#FF7043")

        self._rules = rules

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            idx = pattern.indexIn(text)
            while idx >= 0:
                length = pattern.matchedLength()
                self.setFormat(idx, length, fmt)
                idx = pattern.indexIn(text, idx + length)


# ---------------------------------------------------------------------------
# Main Editor Panel
# ---------------------------------------------------------------------------

class IFCEditorPanel(QtWidgets.QWidget):
    """
    Main dockable widget:
      - Toolbar  (New / Open / Save / Run / Send to BIM / Clear)
      - QSplitter(vertical):  code editor  |  console output
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filepath = None
        self.modified = False

        self._wb_dir = os.path.dirname(os.path.abspath(__file__))
        self._snippets_dir = os.path.join(self._wb_dir, "snippets")
        self._examples_dir = os.path.join(self._wb_dir, "examples")

        self._setup_ui()
        self._load_default_template()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- Toolbar ----
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(16, 16))

        def btn(label, tip, slot, shortcut=None):
            act = toolbar.addAction(label)
            act.setToolTip(tip)
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(QtGui.QKeySequence(shortcut))
            return act

        btn("New",        "New script (Ctrl+N)",          self.new_script,    "Ctrl+N")
        btn("Open",       "Open .py file (Ctrl+O)",       self.open_script,   "Ctrl+O")
        btn("Save",       "Save script (Ctrl+S)",         self.save_script,   "Ctrl+S")
        toolbar.addSeparator()
        btn("Run",        "Run script (F5)",              self.run_script,    "F5")
        btn("Send to BIM","Send model to BIM workbench",  self.send_to_bim)
        btn("Export IFC", "Export model to .ifc file",    self.export_ifc)
        toolbar.addSeparator()
        btn("Clear",      "Clear IFC objects from viewport", self.clear_objects)
        toolbar.addSeparator()

        # Example selector
        toolbar.addWidget(QtWidgets.QLabel(" Example: "))
        self.example_combo = QtWidgets.QComboBox()
        self.example_combo.setMinimumWidth(150)
        self._populate_examples()
        self.example_combo.currentIndexChanged.connect(self._on_example_changed)
        toolbar.addWidget(self.example_combo)

        # Snippet insert dropdown
        toolbar.addWidget(QtWidgets.QLabel("  Snippet: "))
        self.snippet_combo = QtWidgets.QComboBox()
        self.snippet_combo.setMinimumWidth(160)
        self._populate_snippet_combo()
        self.snippet_combo.currentIndexChanged.connect(self._on_snippet_changed)
        toolbar.addWidget(self.snippet_combo)

        main_layout.addWidget(toolbar)

        # ---- Editor fills full width — no sidebar ----
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        font.setPointSize(11)
        self.editor.setFont(font)
        self.editor.setStyleSheet(
            "QPlainTextEdit { background:#1e1e1e; color:#d4d4d4; "
            "selection-background-color:#264f78; border:none; }"
        )
        self.highlighter = IFCSyntaxHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._on_text_changed)
        main_layout.addWidget(self.editor)

        # Status bar
        self.status_bar = QtWidgets.QLabel("Ready")
        self.status_bar.setStyleSheet("padding: 2px 6px; color: #aaaaaa; font-size:9pt;")
        main_layout.addWidget(self.status_bar)

        # Shortcuts
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self).activated.connect(self.run_script)

    def _populate_examples(self):
        self.example_combo.blockSignals(True)
        self.example_combo.clear()
        self.example_combo.addItem("-- select example --", None)
        if os.path.isdir(self._examples_dir):
            for fp in sorted(glob.glob(os.path.join(self._examples_dir, "*.py"))):
                name = os.path.splitext(os.path.basename(fp))[0].replace("_", " ").title()
                self.example_combo.addItem(name, fp)
        self.example_combo.blockSignals(False)

    def _populate_snippet_combo(self):
        """Build flat snippet list: 'Category / Name' → filepath."""
        self.snippet_combo.blockSignals(True)
        self.snippet_combo.clear()
        self.snippet_combo.addItem("-- insert snippet --", None)
        if os.path.isdir(self._snippets_dir):
            for folder in sorted(os.listdir(self._snippets_dir)):
                folder_path = os.path.join(self._snippets_dir, folder)
                if not os.path.isdir(folder_path):
                    continue
                cat = folder.split("_", 1)[-1].replace("_", " ").title()
                for fp in sorted(glob.glob(os.path.join(folder_path, "*.py"))):
                    fname = os.path.splitext(os.path.basename(fp))[0].replace("_", " ").title()
                    self.snippet_combo.addItem(f"{cat} / {fname}", fp)
        self.snippet_combo.blockSignals(False)

    def _on_snippet_changed(self, index):
        filepath = self.snippet_combo.itemData(index)
        if not filepath or not os.path.isfile(filepath):
            return
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            self._insert_snippet(content)
        except Exception as e:
            self._log_error(f"Snippet load error: {e}")
        # Reset combo back to placeholder
        self.snippet_combo.blockSignals(True)
        self.snippet_combo.setCurrentIndex(0)
        self.snippet_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _load_default_template(self):
        tmpl_path = os.path.join(self._wb_dir, "snippets", "00_project", "project_setup.py")
        if os.path.isfile(tmpl_path):
            with open(tmpl_path, encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
        else:
            self.editor.setPlainText(_DEFAULT_TEMPLATE)
        self.modified = False
        self._update_title()

    def new_script(self):
        if self.modified:
            r = QtWidgets.QMessageBox.question(self, "Unsaved changes",
                "Discard current script and start new?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if r != QtWidgets.QMessageBox.Yes:
                return
        self.filepath = None
        self._load_default_template()

    def open_script(self):
        start_dir = os.path.dirname(self.filepath) if self.filepath else ""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open IFC Script", start_dir, "Python Files (*.py);;All Files (*)"
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.filepath = path
                self.modified = False
                self._update_title()
                self._log(f"Opened: {path}")
            except Exception as e:
                self._log_error(f"Open failed: {e}")

    def save_script(self):
        if not self.filepath:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save IFC Script", "", "Python Files (*.py);;All Files (*)"
            )
            if not path:
                return
            self.filepath = path
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.modified = False
            self._update_title()
            self._log(f"Saved: {self.filepath}")
        except Exception as e:
            self._log_error(f"Save failed: {e}")

    # ------------------------------------------------------------------
    # Script execution
    # ------------------------------------------------------------------

    def _get_runner(self):
        """Load ifc_runner by absolute file path."""
        import importlib.util
        runner_path = os.path.join(self._wb_dir, "core", "ifc_runner.py")

        if not os.path.isfile(runner_path):
            raise FileNotFoundError(f"ifc_runner.py not found at: {runner_path}")

        spec   = importlib.util.spec_from_file_location("ifc_runner_wb", runner_path)
        runner = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(runner)
        except Exception as e:
            raise RuntimeError(f"ifc_runner.py failed to load:\n{e}")

        if not hasattr(runner, "run_script"):
            # Show what IS available to help diagnose
            attrs = [a for a in dir(runner) if not a.startswith("_")]
            raise AttributeError(
                f"run_script not found in ifc_runner.py\n"
                f"Available: {attrs}\n"
                f"Path: {runner_path}")

        self._runner = runner
        return runner

    def run_script(self):
        try:
            runner = self._get_runner()
        except Exception as e:
            self._log_error(f"Cannot load ifc_runner: {e}")
            return

        code = self.editor.toPlainText().strip()
        if not code:
            self._log_error("Editor is empty — nothing to run.")
            return

        self._log("Running script...")
        self.status_bar.setText("Running...")
        QtWidgets.QApplication.processEvents()

        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = _FCConsoleRedirector(error=False)
        sys.stderr = _FCConsoleRedirector(error=True)

        try:
            model, error = runner.run_script(code)
        finally:
            sys.stdout = old_out
            sys.stderr = old_err

        if error:
            self._log_error(error)
            self.status_bar.setText("Script error — see Report View")
            return

        # Store model on panel so export/send_to_bim can access it
        self._ifc_model = model

        success, skipped, errors = runner.model_to_freecad(model)

        self._log(f"Done: {success} object(s) shown, {skipped} skipped.")
        if errors:
            for e in errors[:5]:
                self._log_error(f"  skip: {e}")
        self.status_bar.setText(f"OK: {success} IFC objects shown")

    def send_to_bim(self):
        try:
            runner = self._get_runner()
        except Exception as e:
            self._log_error(f"Cannot load ifc_runner: {e}")
            return
        if not getattr(self, "_ifc_model", None):
            self._log_error("No model loaded. Run a script first.")
            return
        self._log("Sending to BIM workbench...")
        ok, err = runner.send_to_bim(self._ifc_model)
        if ok:
            self._log("Model sent to BIM workbench.")
            self.status_bar.setText("Sent to BIM")
        else:
            self._log_error(f"Send to BIM failed:\n{err}")

    def clear_objects(self):
        try:
            runner = self._get_runner()
        except Exception as e:
            self._log_error(f"Cannot load ifc_runner: {e}")
            return
        runner.clear_ifc_objects()
        self._log("IFC preview objects cleared.")
        self.status_bar.setText("Cleared")

    def export_ifc(self):
        try:
            runner = self._get_runner()
        except Exception as e:
            self._log_error(f"Cannot load ifc_runner: {e}")
            return
        if not getattr(self, "_ifc_model", None):
            self._log_error("No model loaded. Run a script first.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export IFC", "", "IFC Files (*.ifc);;All Files (*)"
        )
        if not path:
            return
        ok, err = runner.export_ifc(path, self._ifc_model)
        if ok:
            self._log(f"Exported: {path}")
            self.status_bar.setText(f"Exported: {os.path.basename(path)}")
        else:
            self._log_error(f"Export failed: {err}")

    # ------------------------------------------------------------------
    # Snippet insert
    # ------------------------------------------------------------------

    def _insert_snippet(self, content: str):
        """
        Append snippet at the END of the editor — always after existing code.
        This is the correct behavior: project setup at top, elements below.
        """
        # Strip docstring from snippet — user doesn't need the help text in their script
        lines = content.splitlines()
        # Remove leading docstring block if present
        stripped = []
        in_doc = False
        doc_done = False
        for line in lines:
            if not doc_done:
                stripped_line = line.strip()
                if stripped_line.startswith('"""') and not in_doc:
                    in_doc = True
                    # single-line docstring?
                    if stripped_line.count('"""') >= 2 and len(stripped_line) > 3:
                        in_doc = False
                        doc_done = True
                    continue
                elif in_doc:
                    if '"""' in stripped_line:
                        in_doc = False
                        doc_done = True
                    continue
                else:
                    doc_done = True
            stripped.append(line)
        clean_content = "\n".join(stripped).strip()

        # Move cursor to end and append
        cursor = self.editor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        current_text = self.editor.toPlainText()
        separator = "\n\n" if current_text.strip() else ""
        cursor.insertText(f"{separator}\n# ── snippet ──────────────────────────────\n{clean_content}\n")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        # Scroll to bottom so user sees inserted code
        self.editor.verticalScrollBar().setValue(
            self.editor.verticalScrollBar().maximum()
        )

    # ------------------------------------------------------------------
    # Example combo
    # ------------------------------------------------------------------

    def _on_example_changed(self, index):
        filepath = self.example_combo.itemData(index)
        if not filepath or not os.path.isfile(filepath):
            return
        if self.modified:
            r = QtWidgets.QMessageBox.question(self, "Load Example",
                "Replace current script with example?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if r != QtWidgets.QMessageBox.Yes:
                self.example_combo.blockSignals(True)
                self.example_combo.setCurrentIndex(0)
                self.example_combo.blockSignals(False)
                return
        try:
            with open(filepath, encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.filepath = None
            self.modified = False
            self._update_title()
        except Exception as e:
            self._log_error(f"Example load error: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_text_changed(self):
        self.modified = True
        self._update_title()

    def _update_title(self):
        name = os.path.basename(self.filepath) if self.filepath else "untitled.py"
        prefix = "* " if self.modified else ""
        # dock title updated via parent
        self.setWindowTitle(f"{prefix}IFC Editor — {name}")

    def _log(self, msg: str):
        FreeCAD.Console.PrintMessage(f"[IFC] {msg}\n")

    def _log_error(self, msg: str):
        FreeCAD.Console.PrintError(f"[IFC] {msg}\n")


# ---------------------------------------------------------------------------
# Stdout redirector — sends script print() output to FreeCAD Report View
# ---------------------------------------------------------------------------

class _FCConsoleRedirector:
    def __init__(self, error=False):
        self.error = error

    def write(self, text):
        if text.strip():
            if self.error:
                FreeCAD.Console.PrintError(text)
            else:
                FreeCAD.Console.PrintMessage(text)

    def flush(self):
        pass


# ---------------------------------------------------------------------------
# Default template (fallback if snippet file missing)
# ---------------------------------------------------------------------------

_DEFAULT_TEMPLATE = '''\
"""
IFC Code Editor — new script
=============================
The following are pre-available in your namespace:
  model   - ifcopenshell.file(schema="IFC4")
  api     - ifcopenshell.api
  geom    - ifcopenshell.geom
  util    - ifcopenshell.util

Press F5 or click ▶ Run to see 3D result.
"""

import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Units ---
ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METRES"})

# --- Geometry contexts ---
ctx  = ifcopenshell.api.context.add_context(model, context_type="Model")
body = ifcopenshell.api.context.add_context(model,
    context_type="Model", context_identifier="Body",
    target_view="MODEL_VIEW", parent=ctx)

# --- Spatial structure ---
project  = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject",  name="My Project")
site     = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite",     name="Site")
building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name="Building A")
storey   = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="Level 1")

ifcopenshell.api.spatial.assign_container(model, relating_structure=project,  products=[site])
ifcopenshell.api.spatial.assign_container(model, relating_structure=site,      products=[building])
ifcopenshell.api.spatial.assign_container(model, relating_structure=building,  products=[storey])

# --- Add a wall (edit dimensions below) ---
wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name="Wall-01")
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])
'''


# ---------------------------------------------------------------------------
# Show / hide dock
# ---------------------------------------------------------------------------

_dock = None

def show_editor_panel():
    global _dock
    mw = Gui.getMainWindow()

    existing = mw.findChild(QtWidgets.QDockWidget, "IFCCodeEditorDock")
    if existing:
        existing.show()
        existing.raise_()
        return

    _dock = QtWidgets.QDockWidget("IFC Code Editor", mw)
    _dock.setObjectName("IFCCodeEditorDock")
    _dock.setWidget(IFCEditorPanel())
    _dock.setMinimumWidth(400)
    mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, _dock)
    _dock.show()