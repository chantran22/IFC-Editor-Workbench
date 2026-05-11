"""
Window - IfcWindow with IfcOpeningElement void in host wall.
Requires: storey, body, wall already defined.
Edit: WIN_W, WIN_H, WIN_SILL, WIN_X.
"""

import ifcopenshell.api.void

WIN_W    = 1.2
WIN_H    = 1.0
WIN_SILL = 1.0   # sill height from floor
WIN_X    = 2.0   # X position along wall
WALL_T   = 0.25  # must match host wall thickness

# Opening void
opening_win = ifcopenshell.api.root.create_entity(model,
    ifc_class="IfcOpeningElement", name="OPENING-WIN")
opening_win.Representation = rect_solid(WIN_W, WALL_T + 0.1, WIN_H,
    WIN_X, -0.05, WIN_SILL)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=opening_win, matrix=np.eye(4))
ifcopenshell.api.void.add_opening(model, opening=opening_win, element=wall)

# Window element
window = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWindow",
    name="WIN-01", predefined_type="WINDOW")
window.OverallWidth  = float(WIN_W)
window.OverallHeight = float(WIN_H)
window.Representation = rect_solid(WIN_W - 0.05, 0.1, WIN_H - 0.05,
    WIN_X + 0.025, WALL_T/2 - 0.05, WIN_SILL + 0.025)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=window, matrix=np.eye(4))
ifcopenshell.api.spatial.assign_container(model,
    relating_structure=storey, products=[window])
ifcopenshell.api.void.add_filling(model, opening=opening_win, element=window)
