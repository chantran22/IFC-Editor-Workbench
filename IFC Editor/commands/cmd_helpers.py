import FreeCADGui as Gui
from PySide2 import QtWidgets


def _get_panel():
    mw = Gui.getMainWindow()
    dock = mw.findChild(QtWidgets.QDockWidget, "IFCCodeEditorDock")
    if dock:
        return dock.widget()
    return None


# ---- New ----
class CmdNewScript:
    def GetResources(self):
        return {"MenuText": "New Script", "ToolTip": "New IFC script", "Accel": "Ctrl+N"}
    def Activated(self):
        p = _get_panel()
        if p: p.new_script()
    def IsActive(self): return True

Gui.addCommand("IFC_NewScript", CmdNewScript())


# ---- Open ----
class CmdOpenScript:
    def GetResources(self):
        return {"MenuText": "Open Script", "ToolTip": "Open .py file", "Accel": "Ctrl+O"}
    def Activated(self):
        p = _get_panel()
        if p: p.open_script()
    def IsActive(self): return True

Gui.addCommand("IFC_OpenScript", CmdOpenScript())


# ---- Save ----
class CmdSaveScript:
    def GetResources(self):
        return {"MenuText": "Save Script", "ToolTip": "Save script", "Accel": "Ctrl+S"}
    def Activated(self):
        p = _get_panel()
        if p: p.save_script()
    def IsActive(self): return True

Gui.addCommand("IFC_SaveScript", CmdSaveScript())


# ---- Send to BIM ----
class CmdSendToBIM:
    def GetResources(self):
        return {"MenuText": "Send to BIM", "ToolTip": "Pass IFC model to BIM workbench"}
    def Activated(self):
        p = _get_panel()
        if p: p.send_to_bim()
    def IsActive(self): return True

Gui.addCommand("IFC_SendToBIM", CmdSendToBIM())


# ---- Clear ----
class CmdClearObjects:
    def GetResources(self):
        return {"MenuText": "Clear IFC Objects", "ToolTip": "Remove IFC preview objects from viewport"}
    def Activated(self):
        p = _get_panel()
        if p: p.clear_objects()
    def IsActive(self): return True

Gui.addCommand("IFC_ClearObjects", CmdClearObjects())
