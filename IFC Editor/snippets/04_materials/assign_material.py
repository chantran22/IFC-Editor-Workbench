"""
Assign Material — attach a named material to an IFC element.
Replace 'element' with your variable (wall, column, slab, etc.)
"""

import ifcopenshell.api.material

# --- Edit ---
target_element = wall
material_name  = "Concrete C30/37"

material = ifcopenshell.api.material.add_material(model, name=material_name,
                                                    category="concrete")
ifcopenshell.api.material.assign_material(model, products=[target_element],
                                           material=material)
