# IFC Code Editor Workbench for FreeCAD

Write `ifcopenshell` Python scripts and see the 3D result live in FreeCAD's viewport.
This workbench was built-up by Claude AI's support

## Install

1. Copy `IFC_CodeEditor/` into your FreeCAD `Mod/` directory:
   - Windows: `%APPDATA%\FreeCAD\Mod\`
   - Linux:   `~/.local/share/FreeCAD/Mod/`
   - macOS:   `~/Library/Application Support/FreeCAD/Mod/`

2. Make sure `ifcopenshell` is available to FreeCAD's Python:
   ```
   pip install ifcopenshell
   ```
   Or unzip `ifcopenshell-python-*-win64.zip` and place the `ifcopenshell/` folder
   inside the `IFC_CodeEditor/` directory (portable, no install needed).

3. Restart FreeCAD — select **IFC Code Editor** from the workbench dropdown.

## Layout

```
┌─────────────────┬─────────────────────────────┐
│  Snippet Browser│  Code Editor (top)          │
│  (left)         │  Console / Output (bottom)  │
└─────────────────┴─────────────────────────────┘
         FreeCAD 3D Viewport (separate, existing)
```

## Workflow

1. Write or load a script in the editor
2. Press **F5** (or ▶ Run) → geometry appears in FreeCAD viewport as `Part::Feature` objects
3. Tweak script → Run again → objects update
4. Happy with geometry? Click **⬆ Send to BIM** → passes model to BIM workbench for property editing and IFC export

## Pre-available in every script namespace

| Variable | What it is |
|---|---|
| `model` | `ifcopenshell.file(schema="IFC4")` — fresh each run |
| `api`   | `ifcopenshell.api` |
| `geom`  | `ifcopenshell.geom` |
| `util`  | `ifcopenshell.util` |

## Snippets

Double-click any snippet in the left panel to insert it at the cursor.

| Folder | Contents |
|---|---|
| `00_project` | Full IFC project boilerplate |
| `01_elements` | Wall, Column, Slab, Beam, Door, Window |
| `02_geometry` | Extruded profile, swept solid, BRep |
| `03_properties` | Pset creation and editing |
| `04_materials` | Material assignment |

## Examples

Selectable from the toolbar dropdown:

- `01_simple_wall.py` — single wall with pset and material
- `02_column_grid.py` — parametric 3×4 column grid
- `03_simple_building.py` — full frame: walls + columns + slab

## File Structure

```
IFC_CodeEditor/
├── Init.py           # non-GUI startup, checks ifcopenshell
├── InitGui.py        # workbench registration
├── commands/         # FreeCAD command classes
├── ui/
│   └── editor_panel.py   # main dockable panel
├── core/
│   └── ifc_runner.py     # sandbox exec + geometry bridge
├── snippets/         # .py snippet library
├── examples/         # runnable demo scripts
└── resources/        # icons
```
## Picture demo
<img width="770" height="321" alt="image" src="https://github.com/user-attachments/assets/1243bec7-6571-4691-884f-ede22c10d3aa" />

export to *.ifc  or upload 3dviewer.net can see & retract info of IFC model.
