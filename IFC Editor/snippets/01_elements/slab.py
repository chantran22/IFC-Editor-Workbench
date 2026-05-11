"""
Slab - IfcSlab with rectangular footprint. No shape_builder needed.
Requires: storey, body context already defined.
Edit: width, length, thickness.
"""

import numpy as np
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Parameters ---
WIDTH = 8.0
LNGTH = 12.0
THICK = 0.25

z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
x_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(0.0), float(0.0), float(0.0)))
profile = model.create_entity("IfcRectangleProfileDef",
              ProfileType="AREA", XDim=WIDTH, YDim=LNGTH)
axis3   = model.create_entity("IfcAxis2Placement3D",
              Location=origin, Axis=z_dir, RefDirection=x_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=z_dir, Depth=THICK)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

slab = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSlab", name="SLAB-01")
slab.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[slab])
ifcopenshell.api.geometry.edit_object_placement(model, product=slab, matrix=np.eye(4))
