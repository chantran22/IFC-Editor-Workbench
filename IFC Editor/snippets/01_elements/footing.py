"""
Footing - IfcFooting with rectangular pad profile.
Requires: storey, body context already defined.
Edit: width, length, depth, position.
"""

import numpy as np
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry

# --- Parameters ---
WIDTH  = 1.5    # metres
LNGTH  = 1.5
DEPTH  = 0.5
X      = 0.0
Y      = 0.0
Z      = -0.5   # below ground

z_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(0.0), float(0.0), float(1.0)))
x_dir   = model.create_entity("IfcDirection", DirectionRatios=(float(1.0), float(0.0), float(0.0)))
origin  = model.create_entity("IfcCartesianPoint", Coordinates=(float(X), float(Y), float(Z)))
profile = model.create_entity("IfcRectangleProfileDef",
              ProfileType="AREA", XDim=WIDTH, YDim=LNGTH)
axis3   = model.create_entity("IfcAxis2Placement3D",
              Location=origin, Axis=z_dir, RefDirection=x_dir)
extr    = model.create_entity("IfcExtrudedAreaSolid",
              SweptArea=profile, Position=axis3,
              ExtrudedDirection=z_dir, Depth=DEPTH)
rep     = model.create_entity("IfcShapeRepresentation",
              ContextOfItems=body,
              RepresentationIdentifier="Body",
              RepresentationType="SweptSolid",
              Items=[extr])
shape   = model.create_entity("IfcProductDefinitionShape", Representations=[rep])

footing = ifcopenshell.api.root.create_entity(model, ifc_class="IfcFooting",
              name="FTG-01", predefined_type="PAD_FOOTING")
footing.Representation = shape
ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[footing])
ifcopenshell.api.geometry.edit_object_placement(model, product=footing, matrix=np.eye(4))
