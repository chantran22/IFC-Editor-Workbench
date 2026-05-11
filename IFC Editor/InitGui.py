# -*- coding: utf-8 -*-
# IFC Code Editor Workbench for FreeCAD
# InitGui.py — registers the workbench in FreeCAD GUI

import os
import sys
import FreeCAD
import FreeCADGui as Gui

# Ensure WB root on sys.path as early as possible
# _WB_ROOT = os.path.dirname(os.path.abspath(__file__))
# if _WB_ROOT not in sys.path:
    # sys.path.insert(0, _WB_ROOT)


class IFCCodeEditorWorkbench(Gui.Workbench):
    """IFC Code Editor Workbench — write ifcopenshell scripts, see 3D results."""

    MenuText = "IFC Code Editor"
    ToolTip  = "Write and run ifcopenshell Python scripts with live 3D preview"
    # Icon set in __init__ to ensure path resolves correctly at runtime

    def __init__(self):
        """Initialize the workbench."""
        IFC_wbdir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "IFC_CodeEditor")
        self.__class__.Icon = os.path.join(IFC_wbdir, "resources", "ifc.svg")

    def Initialize(self):
        from commands import (
            cmd_run_script,
            cmd_new_script,
            cmd_open_script,
            cmd_save_script,
            cmd_send_to_bim,
            cmd_clear_objects,
            cmd_show_editor,
        )

        self.commands = [
            "IFC_ShowEditor",
            "IFC_NewScript",
            "IFC_OpenScript",
            "IFC_SaveScript",
            "Separator",
            "IFC_RunScript",
            "IFC_SendToBIM",
            "Separator",
            "IFC_ClearObjects",
        ]

        #self.appendToolbar("IFC Code Editor", self.commands)
        self.appendMenu("IFC Editor", self.commands)

        FreeCAD.Console.PrintMessage("IFC Code Editor workbench loaded.\n")

    def Activated(self):
        """Called when workbench is activated — auto-show editor panel."""
        from editor_panel import show_editor_panel
        show_editor_panel()

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(IFCCodeEditorWorkbench())
