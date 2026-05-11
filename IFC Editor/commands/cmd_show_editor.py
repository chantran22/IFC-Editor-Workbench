import FreeCADGui as Gui

class CmdShowEditor:
    def GetResources(self):
        return {"MenuText": "Show IFC Editor",
                "ToolTip":  "Open the IFC Code Editor panel",
                "Accel":    "Ctrl+Shift+I"}

    def Activated(self):
        from editor_panel import show_editor_panel
        show_editor_panel()

    def IsActive(self):
        return True

Gui.addCommand("IFC_ShowEditor", CmdShowEditor())
