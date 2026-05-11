# -*- coding: utf-8 -*-
# IFC Code Editor Workbench
# Init.py — called by FreeCAD at startup (non-GUI side)

import os
import sys
import FreeCAD

IFC_WB_DIR = os.path.dirname(__file__)

# Ensure WB root is on sys.path so sub-packages (core, ui, commands) resolve
if IFC_WB_DIR not in sys.path:
    sys.path.insert(0, IFC_WB_DIR)

def check_ifcopenshell():
    """Warn if ifcopenshell is not available."""
    try:
        import ifcopenshell
        FreeCAD.Console.PrintMessage(
            f"IFC Code Editor: ifcopenshell {ifcopenshell.version} found.\n"
        )
        return True
    except ImportError:
        FreeCAD.Console.PrintWarning(
            "IFC Code Editor: ifcopenshell not found.\n"
            "Install via: pip install ifcopenshell\n"
            "Or place the ifcopenshell folder inside this workbench directory.\n"
        )
        return False

check_ifcopenshell()
