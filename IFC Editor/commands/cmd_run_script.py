import FreeCADGui as Gui

class CmdRunScript:
    def GetResources(self):
        return {"MenuText": "Run Script",
                "ToolTip":  "Execute the current IFC script (F5)",
                "Accel":    "F5"}

    def Activated(self):
        mw = Gui.getMainWindow()
        from PySide2 import QtWidgets
        dock = mw.findChild(QtWidgets.QDockWidget, "IFCCodeEditorDock")
        if dock:
            panel = dock.widget()
            if panel:
                panel.run_script()

    def IsActive(self):
        return True

Gui.addCommand("IFC_RunScript", CmdRunScript())
