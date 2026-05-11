"""
Column - IfcColumn with circular extruded profile. No shape_builder needed.
Requires: storey, body context already defined.
Edit: radius, height, x, y position.
"""

import numpy as np
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Parameters ---
RADIUS = 0.2    # metres
HEIGHT = 3.5
X      = 0.0
Y      = 0.0

z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
ax2_2d  = model.create_entity("IfcAxis2Placement2D",
              Location=model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0))))
profile = model.create_entity("IfcCircleProfileDef",
              ProfileType="AREA", Radius=RADIUS, Position=ax2_2d)
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(X), float(Y), float(0.0)))
axis3   = model.create_entity("IfcAxis2Placement3D", Location=origin, Axis=z_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=z_dir, Depth=HEIGHT)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

column = ifcopenshell.api.root.create_entity(model, ifc_class="IfcColumn", name="COL-01")
column.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[column])
ifcopenshell.api.geometry.edit_object_placement(model, product=column, matrix=np.eye(4))
