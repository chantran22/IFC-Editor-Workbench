"""
Wall - IfcWall with rectangular extruded profile. No shape_builder needed.
Requires: storey, body context already defined.
Edit: length, height, thickness.
"""

import numpy as np
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Parameters ---
LENGTH = 5.0
HEIGHT = 3.0
THICK  = 0.2

z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
x_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0), float(0.0)))
profile = model.create_entity("IfcRectangleProfileDef",
              ProfileType="AREA", XDim=LENGTH, YDim=THICK)
axis3   = model.create_entity("IfcAxis2Placement3D",
              Location=origin, Axis=z_dir, RefDirection=x_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=z_dir, Depth=HEIGHT)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name="WALL-01")
wall.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])
ifcopenshell.api.geometry.edit_object_placement(model, product=wall, matrix=np.eye(4))
