# -*- coding: utf-8 -*-
"""IFC Runner — sandbox execution + FreeCAD display + export."""

import traceback
import sys
import os
import tempfile
import FreeCAD


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class IFCRunnerState:
    ifc_model   = None
    last_script = ""
    last_error  = ""

_state = IFCRunnerState()

def get_state():
    return _state


# ---------------------------------------------------------------------------
# set_color — defined before build_namespace so it can be referenced
# ---------------------------------------------------------------------------

def set_color(obj_name_or_label, r, g, b, transparency=0, doc=None):
    """
    Set display color of a viewport object.
    r,g,b: 0.0-1.0 or 0-255 (auto-detected)
    transparency: 0=solid, 100=invisible
    Example:
        set_color("IfcWall_WALL-01", 1.0, 0.0, 0.0)
        set_color("IfcWall_WALL-01", 255, 128, 0, transparency=20)
    """
    try:
        import FreeCADGui as Gui
        doc = doc or FreeCAD.ActiveDocument
        vp = Gui.ActiveDocument.getObject(obj_name_or_label)
        if vp is None:
            for obj in doc.Objects:
                if obj.Label == obj_name_or_label:
                    vp = Gui.ActiveDocument.getObject(obj.Name)
                    break
        if vp is None:
            FreeCAD.Console.PrintWarning(f"[IFC] set_color: '{obj_name_or_label}' not found\n")
            return
        if r > 1 or g > 1 or b > 1:
            r, g, b = r/255.0, g/255.0, b/255.0
        vp.ShapeColor   = (float(r), float(g), float(b))
        vp.Transparency = int(transparency)
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"[IFC] set_color error: {e}\n")


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------

def build_namespace():
    try:
        import ifcopenshell
        import ifcopenshell.api
        import ifcopenshell.geom
        import ifcopenshell.util.element
        import ifcopenshell.util.placement

        import importlib.util as _ilu
        _wb_dir = os.path.dirname(__file__)

        _spec = _ilu.spec_from_file_location("ifc_helpers",
                    os.path.join(_wb_dir, "ifc_helpers.py"))
        _helpers = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_helpers)

        _spec2 = _ilu.spec_from_file_location("ifc_tools_fresh",
                     os.path.join(_wb_dir, "ifc_tools.py"))
        _ifc_tools = _ilu.module_from_spec(_spec2)
        _spec2.loader.exec_module(_ifc_tools)

        _model = ifcopenshell.file(schema="IFC4")
        _ctx   = _helpers.IFCContext(_model)

        ns = {
            "ifcopenshell" : ifcopenshell,
            "api"          : ifcopenshell.api,
            "geom"         : ifcopenshell.geom,
            "util"         : ifcopenshell.util,
            "model"        : _model,
            "get_psets"    : ifcopenshell.util.element.get_psets,
            "get_type"     : ifcopenshell.util.element.get_type,
            "FreeCAD"      : FreeCAD,
            "np"           : __import__("numpy"),
            "IFCContext"   : _helpers.IFCContext,
            "ctx"          : _ctx,
            "IFCTools"     : _ifc_tools.IFCTools,
            "tools"        : _ifc_tools.IFCTools(_ctx),
            "set_color"    : set_color,
        }
        return ns, None
    except ImportError as e:
        return None, f"ifcopenshell not available: {e}"


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------

def run_script(code: str):
    ns, err = build_namespace()
    if err:
        return None, err
    _state.last_script = code
    try:
        exec(compile(code, "<ifc_editor>", "exec"), ns)
    except Exception:
        tb = traceback.format_exc()
        _state.last_error = tb
        return None, tb
    model = ns.get("model")
    if model is None:
        msg = "'model' variable not found."
        _state.last_error = msg
        return None, msg
    _state.ifc_model  = model
    _state.last_error = ""
    return model, None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_doc(doc_name="IFC_Preview"):
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument(doc_name)
    return doc


def _write_temp_ifc(model):
    tmp = tempfile.NamedTemporaryFile(suffix=".ifc", delete=False)
    tmp.close()
    model.write(tmp.name)
    return tmp.name


def _find_ifc_importer():
    for mod_name in ("ifc_tools", "BimIfcImport", "importIFC"):
        try:
            mod = __import__(mod_name)
            return mod, mod_name
        except ImportError:
            continue
    return None, None


def clear_ifc_objects(doc=None):
    doc = doc or _get_or_create_doc()
    to_remove = [obj.Name for obj in doc.Objects
                 if hasattr(obj, "IFCClass") or obj.TypeId == "Mesh::Feature"]
    for name in to_remove:
        try: doc.removeObject(name)
        except Exception: pass
    doc.recompute()


# ---------------------------------------------------------------------------
# IFC class colors
# ---------------------------------------------------------------------------

_IFC_COLORS = {
    "IfcWall"              : (0.85, 0.82, 0.75),
    "IfcWallStandardCase"  : (0.85, 0.82, 0.75),
    "IfcSlab"              : (0.75, 0.75, 0.75),
    "IfcColumn"            : (0.70, 0.70, 0.75),
    "IfcBeam"              : (0.60, 0.65, 0.75),
    "IfcFooting"           : (0.60, 0.55, 0.45),
    "IfcDoor"              : (0.65, 0.45, 0.25),
    "IfcWindow"            : (0.65, 0.85, 0.95),
    "IfcRoof"              : (0.60, 0.30, 0.25),
    "IfcStair"             : (0.80, 0.75, 0.65),
    "IfcRailing"           : (0.50, 0.50, 0.55),
    "IfcPipeSegment"       : (0.70, 0.70, 0.20),
    "IfcOpeningElement"    : (0.90, 0.90, 0.50),
    "IfcSpace"             : (0.70, 0.85, 0.95),
}
_IFC_TRANSPARENCY = {
    "IfcWindow" : 60,
    "IfcSpace"  : 80,
}


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def model_to_freecad(model, doc=None, clear_first=True):
    _state.ifc_model = model
    doc = doc or _get_or_create_doc()
    if clear_first:
        clear_ifc_objects(doc)

    importer, mode = _find_ifc_importer()
    if importer is not None:
        try:
            return _display_via_importer(model, doc, importer, mode)
        except Exception as e:
            FreeCAD.Console.PrintMessage(f"[IFC] {mode} failed ({e}), using mesh.\n")

    FreeCAD.Console.PrintMessage("[IFC] Using mesh preview.\n")
    return _display_via_mesh(model, doc)


def _display_via_importer(model, doc, importer, mode):
    tmp_path = _write_temp_ifc(model)
    try:
        if mode == "ifc_tools":
            importer.load_ifcfile(tmp_path, doc)
        else:
            importer.insert(tmp_path, doc.Name)
        doc.recompute()
        try:
            import FreeCADGui as Gui
            Gui.SendMsgToActiveView("ViewFit")
        except Exception:
            pass
        return len(doc.Objects), 0, []
    finally:
        try: os.unlink(tmp_path)
        except Exception: pass


def _display_via_mesh(model, doc):
    try:
        import ifcopenshell.geom
        import Mesh
        import FreeCADGui as Gui
    except ImportError as e:
        return 0, 0, [f"Missing module: {e}"]

    settings = ifcopenshell.geom.settings()
    settings.set(settings.WELD_VERTICES, True)
    settings.set(settings.USE_WORLD_COORDS, True)

    success = 0; skipped = 0; errors = []
    products = [p for p in model.by_type("IfcProduct")
                if getattr(p, "Representation", None) is not None]

    for product in products:
        try:
            shape_data = ifcopenshell.geom.create_shape(settings, product)
            geom       = shape_data.geometry
            verts = list(zip(geom.verts[0::3], geom.verts[1::3], geom.verts[2::3]))
            faces = list(zip(geom.faces[0::3], geom.faces[1::3], geom.faces[2::3]))
            if not verts or not faces:
                skipped += 1; continue

            mesh = Mesh.Mesh()
            for tri in faces:
                try:
                    pts = [FreeCAD.Vector(*verts[i]) for i in tri]
                    mesh.addFacet(pts[0], pts[1], pts[2])
                except Exception: continue

            if mesh.CountFacets == 0:
                skipped += 1; continue

            label = f"{product.is_a()}_{product.Name or product.id()}".replace(" ", "_")
            obj = doc.addObject("Mesh::Feature", label)
            obj.Mesh = mesh
            obj.addProperty("App::PropertyString", "IFCClass",    "IFC", "IFC class")
            obj.addProperty("App::PropertyString", "IFCGlobalId", "IFC", "IFC GlobalId")
            obj.IFCClass    = product.is_a()
            obj.IFCGlobalId = str(getattr(product, "GlobalId", ""))

            # Apply color by IFC class
            try:
                color = _IFC_COLORS.get(product.is_a(), (0.75, 0.75, 0.75))
                transp = _IFC_TRANSPARENCY.get(product.is_a(), 0)
                vp = Gui.ActiveDocument.getObject(obj.Name)
                if vp:
                    vp.ShapeColor   = color
                    vp.Transparency = transp
            except Exception:
                pass

            success += 1
        except Exception as e:
            skipped += 1
            errors.append(f"{product.is_a()} #{product.id()}: {e}")

    doc.recompute()
    try:
        import FreeCADGui as Gui
        Gui.SendMsgToActiveView("ViewFit")
    except Exception: pass
    return success, skipped, errors


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_ifc(filepath, model=None):
    model = model or _state.ifc_model
    if model is None:
        return False, "No model. Run a script first."
    try:
        model.write(filepath)
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Send to BIM
# ---------------------------------------------------------------------------

def send_to_bim(model=None):
    model = model or _state.ifc_model
    if model is None:
        return False, "No model. Run a script first."

    tmp_path = _write_temp_ifc(model)
    try:
        import FreeCADGui as Gui
        importer, mode = _find_ifc_importer()
        bim_doc = FreeCAD.newDocument("IFC_BIM")

        if mode == "ifc_tools":
            importer.load_ifcfile(tmp_path, bim_doc)
        elif mode in ("BimIfcImport", "importIFC"):
            importer.insert(tmp_path, bim_doc.Name)
        else:
            save_path = os.path.join(FreeCAD.getUserAppDataDir(), "ifc_export.ifc")
            import shutil
            shutil.copy(tmp_path, save_path)
            FreeCAD.Console.PrintMessage(f"[IFC] Saved to: {save_path}\n")
            return True, None

        bim_doc.recompute()
        try: Gui.activateWorkbench("BIMWorkbench")
        except Exception:
            try: Gui.activateWorkbench("ArchWorkbench")
            except Exception: pass
        Gui.SendMsgToActiveView("ViewFit")
        return True, None

    except Exception:
        return False, traceback.format_exc()
    finally:
        try: os.unlink(tmp_path)
        except Exception: pass