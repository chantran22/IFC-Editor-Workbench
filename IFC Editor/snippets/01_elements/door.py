"""
Door - IfcDoor with IfcOpeningElement void in host wall.
Requires: storey, body, wall already defined.
Edit: DOOR_W, DOOR_H, DOOR_X (position along wall).
"""

import ifcopenshell.api.void

DOOR_W = 1.0   # metres
DOOR_H = 2.1
DOOR_X = 1.0   # X position along wall
WALL_T = 0.25  # must match host wall thickness

# Opening void
opening_door = ifcopenshell.api.root.create_entity(model,
    ifc_class="IfcOpeningElement", name="OPENING-DOOR")
opening_door.Representation = rect_solid(DOOR_W, WALL_T + 0.1, DOOR_H,
    DOOR_X, -0.05, 0)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=opening_door, matrix=np.eye(4))
ifcopenshell.api.void.add_opening(model, opening=opening_door, element=wall)

# Door element
door = ifcopenshell.api.root.create_entity(model, ifc_class="IfcDoor",
    name="DOOR-01", predefined_type="DOOR")
door.OverallWidth  = float(DOOR_W)
door.OverallHeight = float(DOOR_H)
door.Representation = rect_solid(DOOR_W - 0.05, WALL_T, DOOR_H - 0.05,
    DOOR_X + 0.025, 0, 0.025)
ifcopenshell.api.geometry.edit_object_placement(model,
    product=door, matrix=np.eye(4))
ifcopenshell.api.spatial.assign_container(model,
    relating_structure=storey, products=[door])
ifcopenshell.api.void.add_filling(model, opening=opening_door, element=door)
