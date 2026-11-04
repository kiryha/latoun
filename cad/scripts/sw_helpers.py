"""Small SOLIDWORKS 2026 COM helpers. Geometric arguments are millimeters."""
import math
from pathlib import Path
import pythoncom
import win32com.client as com
from win32com.client import makepy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'solidworks' / '004'
INSTALL = Path(r'D:\programs\SOLIDWORKS\SOLIDWORKS')
bindings = None


def require(value, message):
    if not value:
        raise RuntimeError(message)
    return value


def interface(obj, name):
    if obj is None:
        return None
    cls = getattr(bindings, name)
    return cls(obj._oleobj_.QueryInterface(cls.CLSID, pythoncom.IID_IDispatch))


def connect():
    global bindings
    pythoncom.CoInitialize()
    lib = pythoncom.LoadTypeLib(str(INSTALL / 'sldworks.tlb'))
    guid, lcid, _, major, minor, _ = lib.GetLibAttr()
    try:
        bindings = com.gencache.GetModuleForTypelib(guid, lcid, major, minor)
    except ImportError:
        makepy.GenerateFromTypeLibSpec(str(INSTALL / 'sldworks.tlb'), bForDemand=0)
        bindings = com.gencache.GetModuleForTypelib(guid, lcid, major, minor)
    sw = bindings.ISldWorks(com.Dispatch('SldWorks.Application')._oleobj_)
    require(sw.RevisionNumber().startswith('34.'), 'SOLIDWORKS 2026 required')
    sw.Visible = True
    print('SOLIDWORKS', sw.RevisionNumber(), flush=True)
    return sw


def new_document(sw, kind=1):
    template = sw.GetDocumentTemplate(kind, '', 0, 0., 0.)
    require(template and Path(template).exists(), 'Missing document template')
    doc = interface(require(sw.NewDocument(template, 0, 0., 0.), 'NewDocument failed'), 'IModelDoc2')
    doc.SetUnits(0, 0, 0, 3, False)
    return doc


def feature(doc, name):
    return interface(interface(doc, 'IPartDoc').FeatureByName(name), 'IFeature')


def select(doc, name, kind, append=False, mark=0):
    require(doc.Extension.SelectByID2(name, kind, 0., 0., 0., append, mark, None, 0),
            'Cannot select ' + name)


def offset_plane(doc, z, name, base='Front Plane'):
    if abs(z) < 1e-12:
        return base
    doc.ClearSelection2(True)
    select(doc, base, 'PLANE')
    plane = doc.FeatureManager.InsertRefPlane(8 | (256 if z < 0 else 0), abs(z)/1000, 0, 0., 0, 0.)
    require(plane, 'Offset plane failed')
    feat = interface(doc.FeatureByPositionReverse(0), 'IFeature')
    feat.Name = name
    return name


def start_sketch(doc, name, z=0, base='Front Plane'):
    plane = offset_plane(doc, z, name + '_Plane', base)
    doc.ClearSelection2(True)
    select(doc, plane, 'PLANE')
    sm = doc.SketchManager
    sm.InsertSketch(True)
    sm.AddToDB = True
    return sm


def finish_sketch(doc, name, entities, define=True):
    sm = doc.SketchManager
    sm.AddToDB = False
    doc.ClearSelection2(True)
    if define:
        datum = sm.CreatePoint(0., 0., 0.)
        datum.Select4(False, None)
        doc.SketchAddConstraints('sgFIXED')
        doc.ClearSelection2(True)
        # Native automatic dimensions and relations, rather than fixing every point.
        sm.FullyDefineSketch(True, True, 2 | 4 | 8 | 512, True, 1, datum, 1, datum, 0, 0)
    sketch = interface(sm.ActiveSketch, 'ISketch')
    status = sketch.GetConstrainedStatus()
    sm.InsertSketch(True)
    feat = interface(doc.FeatureByPositionReverse(0), 'IFeature')
    feat.Name = name
    print('  Sketch', name, 'constraint status', status, flush=True)
    return feat


def line(sm, a, b):
    return require(sm.CreateLine(a[0]/1000, a[1]/1000, 0., b[0]/1000, b[1]/1000, 0.), 'Line failed')


def polygon(sm, points):
    return [line(sm, a, b) for a, b in zip(points, points[1:] + points[:1])]


def rounded_rect(sm, w, h, r):
    entities = []
    for cx, cy, ang in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),
                        (-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        a, b = math.radians(ang), math.radians(ang+90)
        entities.append(require(sm.CreateArc(cx/1000,cy/1000,0.,
            (cx+r*math.cos(a))/1000,(cy+r*math.sin(a))/1000,0.,
            (cx+r*math.cos(b))/1000,(cy+r*math.sin(b))/1000,0.,1), 'Arc failed'))
    entities += [line(sm,a,b) for a,b in [
        ((w/2,-h/2+r),(w/2,h/2-r)),((w/2-r,h/2),(-w/2+r,h/2)),
        ((-w/2,h/2-r),(-w/2,-h/2+r)),((-w/2+r,-h/2),(w/2-r,-h/2))]]
    return entities


def circle(sm, d, x=0, y=0):
    return require(sm.CreateCircleByRadius(x/1000,y/1000,0.,d/2000), 'Circle failed')


def rr_sketch(doc, name, z, w, h, r):
    sm = start_sketch(doc,name,z)
    return finish_sketch(doc,name,rounded_rect(sm,w,h,r))


def loft(doc, sketches, name, cut=False):
    doc.ClearSelection2(True)
    for i,sk in enumerate(sketches):
        require(sk.Select2(i != 0,1), 'Loft profile selection failed')
    if cut:
        f = doc.FeatureManager.InsertCutBlend(False,False,False,1.,0,0,False,0.,0.,0,True,True)
    else:
        f = doc.FeatureManager.InsertProtrusionBlend2(False,False,False,1.,0,0,0.,0.,
            False,False,False,0.,0.,0,True,True,True,0)
    require(f, name + ' loft failed')
    f.Name = name
    doc.ClearSelection2(True)
    print('  Feature',name,flush=True)
    return f


def extrude(doc, sketch, depth, name, reverse=False):
    doc.ClearSelection2(True)
    require(sketch.Select2(False,0), 'Extrude profile selection failed')
    f=doc.FeatureManager.FeatureExtrusion3(True,False,reverse,0,0,depth/1000,0.,
        False,False,False,False,0.,0.,False,False,False,False,True,True,True,0,0.,False)
    require(f,name+' extrusion failed').Name=name
    return f


def cut_extrude(doc, sketch, depth, name, both=False):
    doc.ClearSelection2(True)
    require(sketch.Select2(False,0),'Cut profile selection failed')
    f=doc.FeatureManager.FeatureCut4(not both,False,False,0,0,depth/1000,depth/1000,
        False,False,False,False,0.,0.,False,False,False,False,False,
        True,True,False,False,False,0,0.,False,True)
    require(f,name+' cut failed').Name=name
    return f


def revolve(doc, name, profile):
    # Right Plane local X maps to global -Z and local Y to global Y.
    # Use Front Plane local X=radial X and Y=axial Y; assembly rotation is avoided
    # by sketching on the Top Plane, whose local Y maps to -Z.
    sm=start_sketch(doc,name+'_Profile',0,'Top Plane')
    ents=polygon(sm,[(radius,-z) for z,radius in profile])
    axis=sm.CreateCenterLine(0.,0.,0.,0.,-.1,0.)
    sk=finish_sketch(doc,name+'_Profile',ents+[axis])
    doc.ClearSelection2(True)
    sk.Select2(False,0)
    axis.Select4(True, None)
    # Axis mark 16 is required by the revolve API.
    sd=interface(doc.SelectionManager,'ISelectionMgr').CreateSelectData()
    sd.Mark=16
    doc.ClearSelection2(True)
    sk.Select2(False,0)
    require(axis.Select4(True,sd),'Revolve axis selection failed')
    f=doc.FeatureManager.FeatureRevolve2(True,True,False,False,False,False,0,0,
        2*math.pi,0.,False,False,0.,0.,0,0.,0.,True,True,True)
    require(f,name+' revolve failed').Name=name
    return f


def part_check(doc, names):
    require(doc.EditRebuild3(),'Part rebuild failed')
    bodies=interface(doc,'IPartDoc').GetBodies2(0,False)
    require(bodies and len(bodies)==1,'Expected one solid body')
    body=interface(bodies[0],'IBody2')
    require(body.Check()==1,'Invalid solid')
    approx_bounds=[v*1000 for v in body.GetBodyBox()]
    bounds=[]
    for direction in [(-1.,0.,0.),(0.,-1.,0.),(0.,0.,-1.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]:
        ok,x,y,z=body.GetExtremePoint(*direction,0.,0.,0.)
        require(ok,'Exact bound evaluation failed')
        axis=next(i for i,v in enumerate(direction) if v)
        bounds.append((x,y,z)[axis]*1000)
    volume=body.GetMassProperties(1.)[3]*1e9
    checked=[]
    for name in names:
        f=feature(doc,name)
        require(f,'Missing native feature '+name)
        err,warn=f.GetErrorCode2()
        require(err==0,f'Feature {name} error {err}, warning {warn}')
        checked.append({'name':name,'type':f.GetTypeName2(),'error':err,'warning':warn})
    return {'bodies':1,'valid':True,'bounds_mm':bounds,'approx_bounds_mm':approx_bounds,
            'volume_mm3':volume,'features':checked}


def save_new(sw,doc,path,kind=1):
    path=Path(path)
    require(not path.exists(),'Refusing to overwrite '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    doc.ShowNamedView2('*Isometric',7)
    doc.ViewZoomtofit2()
    ok,err,warn=doc.Extension.SaveAs(str(path),0,1,None,0,0)
    require(ok and err==0 and path.exists(),f'Save failed {path}: {err}, {warn}')
    print('SAVED',path.name,flush=True)
    return {'errors':err,'warnings':warn}


def reopen(sw,path,kind=1):
    doc,err,warn=sw.OpenDoc6(str(path),kind,1,'',0,0)
    require(doc and err==0,f'Open failed: {path}, {err}, {warn}')
    return interface(doc,'IModelDoc2')
