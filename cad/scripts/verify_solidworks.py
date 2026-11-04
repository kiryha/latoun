"""Isolated native-feature smoke test; never opens or overwrites product designs.

Run with .venv/Scripts/python.exe scripts/verify_solidworks.py.
Signatures verified against the installed SOLIDWORKS 2026 interop assemblies.
"""
import json
import math
import sys
import faulthandler
from pathlib import Path
from datetime import datetime

import pythoncom
import win32com.client as com
from win32com.client import makepy

ROOT = Path(__file__).resolve().parents[1]
INSTALL = Path(r"D:\programs\SOLIDWORKS\SOLIDWORKS")
RUN = ROOT / "output" / "verification" / datetime.now().strftime("%Y%m%d_%H%M%S")
RUN.mkdir(parents=True, exist_ok=False)
report = {"status": "started", "test_part": str(RUN / "automation_smoke.SLDPRT")}
faulthandler.dump_traceback_later(45, repeat=True)
created_title = None
old_dimension_prompt = None


def require(value, message):
    if not value:
        raise RuntimeError(message)
    return value


def interface(obj, name):
    if obj is None:
        return None
    cls = getattr(bindings, name)
    return cls(obj._oleobj_.QueryInterface(cls.CLSID, pythoncom.IID_IDispatch))


def inspect_part(model):
    print("Inspect: rebuild", flush=True)
    model = interface(model, "IModelDoc2")
    require(model.EditRebuild3(), "Rebuild failed")
    print("Inspect: bodies", flush=True)
    bodies = interface(model, "IPartDoc").GetBodies2(0, False)
    require(bodies and len(bodies) == 1, "Expected one solid body")
    body = interface(bodies[0], "IBody2")
    # The current installation stalls in Check3. The documented older Check
    # returns 1 for a valid body, 0 for an invalid body.
    check = body.Check()
    print("Inspect: body valid", check, flush=True)
    require(check == 1, "Body is invalid")
    volume = body.GetMassProperties(1.0)[3]
    print("Inspect: volume", volume, flush=True)
    require(math.isclose(volume, math.pi * .01**2 * .005, rel_tol=1e-7),
            f"Unexpected volume: {volume} m^3")
    features = []
    feature = interface(model.FirstFeature(), "IFeature")
    while feature:
        require(len(features) < 100, "Feature traversal exceeded expected count")
        print("Inspect feature:", feature.Name, flush=True)
        features.append({"name": feature.Name, "type": feature.GetTypeName2(),
                         "error": feature.GetErrorCode2()})
        require(features[-1]["error"][0] == 0, f"Feature error: {features[-1]}")
        feature = interface(feature.GetNextFeature(), "IFeature")
    require(any(f["type"] == "Boss" for f in features), "Native boss feature missing")
    sketch_feature = interface(interface(model, "IPartDoc").FeatureByName("Test_Profile"), "IFeature")
    sketch = interface(sketch_feature.GetSpecificFeature2(), "ISketch")
    print("Inspect: sketch constraints", flush=True)
    constrained = sketch.GetConstrainedStatus()
    require(constrained == com.constants.swFullyConstrained,
            f"Sketch not fully defined: {constrained}")
    require(math.isclose(interface(model.Parameter("D1@Test_Profile"), "IDimension").SystemValue, .02,
                         abs_tol=1e-10), "Diameter dimension mismatch")
    require(math.isclose(interface(model.Parameter("D1@Test_Extrude"), "IDimension").SystemValue, .005,
                         abs_tol=1e-10), "Extrusion dimension mismatch")
    return {"solid_bodies": len(bodies), "body_check": check,
            "volume_mm3": volume * 1e9, "sketch_status": constrained,
            "features": features}


pythoncom.CoInitialize()
try:
    for library in ("sldworks.tlb", "swconst.tlb"):
        makepy.GenerateFromTypeLibSpec(str(INSTALL / library), bForDemand=0)
    library = pythoncom.LoadTypeLib(str(INSTALL / "sldworks.tlb"))
    guid, lcid, _, major, minor, _ = library.GetLibAttr()
    bindings = com.gencache.GetModuleForTypelib(guid, lcid, major, minor)
    sw = bindings.ISldWorks(com.Dispatch("SldWorks.Application")._oleobj_)
    report["revision"] = sw.RevisionNumber()
    report["initial_document_count"] = sw.GetDocumentCount()
    print("Connected:", report["revision"], flush=True)
    sw.Visible = True
    if "--show-session" in sys.argv:
        report["status"] = "session_shown"
        sys.exit(0)
    if "--inspect-session" in sys.argv:
        report["inspection"] = inspect_part(sw.ActiveDoc)
        report["status"] = "inspected"
        sys.exit(0)
    old_dimension_prompt = sw.GetUserPreferenceToggle(com.constants.swInputDimValOnCreate)
    sw.SetUserPreferenceToggle(com.constants.swInputDimValOnCreate, False)
    require(report["revision"].startswith("34."), "Expected SOLIDWORKS 2026")
    template = sw.GetDocumentTemplate(com.constants.swDocPART, "", 0, 0.0, 0.0)
    report["part_template"] = template
    require(template and Path(template).is_file(), "No usable default part template")
    model = require(sw.NewDocument(template, 0, 0.0, 0.0), "NewDocument failed")
    print("Created isolated test document", flush=True)
    model = interface(model, "IModelDoc2")
    created_title = model.GetTitle()
    model.SetUnits(com.constants.swMM, 0, 0, 3, False)
    print("Set millimeter units", flush=True)
    plane = interface(model.FirstFeature(), "IFeature")
    while plane and plane.GetTypeName2() != "RefPlane":
        plane = interface(plane.GetNextFeature(), "IFeature")
    require(plane, "No reference plane")
    require(plane.Select2(False, 0), "Plane selection failed")
    manager = model.SketchManager
    manager.InsertSketch(True)
    print("Started sketch", flush=True)
    circle = require(manager.CreateCircleByRadius(0.0, 0.0, 0.0, .01), "Circle failed")
    center = interface(interface(circle, "ISketchArc").GetCenterPoint2(), "ISketchPoint")
    model.ClearSelection2(True)
    require(center.Select4(False, None), "Center selection failed")
    model.SketchAddConstraints("sgFIXED")
    print("Constrained center", flush=True)
    model.ClearSelection2(True)
    require(circle.Select4(False, None), "Circle selection failed")
    display_dim = interface(require(model.AddDiameterDimension2(.015, .015, 0.0), "Dimension failed"), "IDisplayDimension")
    print("Added diameter dimension", flush=True)
    dim = display_dim.GetDimension2(0)
    require(dim.SetSystemValue3(.02, com.constants.swSetValue_InThisConfiguration, None) == 0,
            "Set diameter failed")
    manager.InsertSketch(True)
    sketch_feature = interface(model.FeatureByPositionReverse(0), "IFeature")
    require(sketch_feature.GetTypeName2() == "ProfileFeature", "Expected native sketch")
    sketch_feature.Name = "Test_Profile"
    model.ClearSelection2(True)
    require(sketch_feature.Select2(False, 0), "Sketch selection failed")
    boss = require(model.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, .005, 0.0,
        False, False, False, False, 0.0, 0.0,
        False, False, False, False, True, True, True, 0, 0.0, False), "Extrusion failed")
    boss.Name = "Test_Extrude"
    print("Created extrusion", flush=True)
    report["before_save"] = inspect_part(model)
    part_path = Path(report["test_part"])
    require(not part_path.exists(), "Refusing to overwrite test part")
    saved, errors, warnings = model.Extension.SaveAs(str(part_path), 0, 1, None)
    created_title = model.GetTitle()
    report["save"] = {"ok": saved, "errors": errors, "warnings": warnings}
    require(saved and errors == 0 and part_path.is_file(), "Save failed")
    sw.CloseDoc(model.GetTitle())
    created_title = None
    reopened, errors, warnings = sw.OpenDoc6(str(part_path), 1, 1, "")
    report["reopen"] = {"errors": errors, "warnings": warnings}
    require(reopened and errors == 0, "Reopen failed")
    created_title = reopened.GetTitle()
    report["after_reopen"] = inspect_part(reopened)
    sw.CloseDoc(reopened.GetTitle())
    created_title = None
    report["status"] = "passed"
except Exception as exc:
    report["status"] = "failed"
    report["error"] = repr(exc)
    raise
finally:
    faulthandler.cancel_dump_traceback_later()
    if old_dimension_prompt is not None:
        sw.SetUserPreferenceToggle(com.constants.swInputDimValOnCreate, old_dimension_prompt)
    if created_title is not None:
        sw.CloseDoc(created_title)
    (RUN / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    pythoncom.CoUninitialize()
