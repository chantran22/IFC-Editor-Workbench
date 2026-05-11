"""
Add Pset — attach a property set to any IFC element.
Replace 'element' with your variable name (wall, column, etc.)
"""

import ifcopenshell.api.pset

# --- Edit: target element and properties ---
target_element = wall   # change to your variable

pset = ifcopenshell.api.pset.add_pset(model, product=target_element,
                                       name="Pset_WallCommon")
ifcopenshell.api.pset.edit_pset(model, pset=pset, properties={
    "IsExternal"       : True,
    "LoadBearing"      : True,
    "FireRating"       : "REI120",
    "ThermalTransmittance": 0.3,
})
