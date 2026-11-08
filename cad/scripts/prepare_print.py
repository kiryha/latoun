"""Create approved SLA test items from saved version-003 solids."""
import argparse
import hashlib
import json
import struct
from collections import Counter
import sw_helpers as h
from sw_helpers import *
from build_parts import move_body
from export_houdini import check_stl

SOURCE=ROOT/'output/003/solidworks'
TARGET=ROOT/'output/004'
JOBS={
    '1gang_print_plate': [('1gang_plate','1gang_plate_metal'),('1gang_plate_screws','lower_fixing_head'),('1gang_plate_screws','upper_fixing_head')],
    '1gang_print_inner': [('1gang_slot1_switch','switch_insert'),('1gang_slot1_switch','switch_bezel')],
    '1gang_print_actuator': [('1gang_slot1_switch','switch_stem'),('1gang_slot1_switch','switch_grip')],
    '1gang_print_dimmer': [('1gang_slot1_dimmer',n) for n in ('dimmer_insert','dimmer_base','dimmer_collar','dimmer_grip','dimmer_cap')],
}


def hashes():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.iterdir() if p.is_file()}


def checked(doc):
    require(doc.EditRebuild3(),'Rebuild failed')
    result=solid_geometry(doc)
    require(result['solid_count']==1,'Print item must be one solid')
    f=interface(doc.FirstFeature(),'IFeature')
    while f:
        error,warning=f.GetErrorCode2()
        require(error==0,'Feature error: '+f.Name)
        f=interface(f.GetNextFeature(),'IFeature')
    return result


def mesh_topology(path):
    edges=Counter();parents={}
    def find(v):
        parents.setdefault(v,v)
        while parents[v]!=v:
            parents[v]=parents[parents[v]];v=parents[v]
        return v
    for row in struct.iter_unpack('<12fH',path.read_bytes()[84:]):
        vertices=[tuple(round(x,5) for x in row[i:i+3]) for i in (3,6,9)]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            if a==b:continue
            edges[tuple(sorted((a,b)))]+=1
            parents[find(a)]=find(b)
    defects=sum(n!=2 for n in edges.values())
    components=len({find(v) for v in parents})
    require(defects==0 and components==1,'STL must be closed and connected')
    return {'open_or_nonmanifold_edges':defects,'connected_components':components,'vertex_weld_precision_mm':.00001}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='+',choices=list(JOBS))
    args=parser.parse_args()
    baseline=hashes()
    report_path=TARGET/'validation/print_validation.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {'units':'mm','clearance_added_mm':0,'heads_translation_z_mm':-.30,'items':{}}
    sw=connect()
    require(not h.initial_documents,'Close pre-existing documents before print preparation')
    settings=[('Integer',75,214),('Integer',78,3),('Integer',211,0),('Double',2,.000005),('Double',3,math.radians(5)),('Toggle',69,True),('Toggle',70,False),('Toggle',71,True),('Toggle',191,False),('Toggle',72,True),('Toggle',73,False)]
    previous=[]
    try:
        for kind,key,value in settings:
            suffix=kind if kind=='Toggle' else kind+'Value'
            getter=getattr(sw,'GetUserPreference'+suffix);setter=getattr(sw,'SetUserPreference'+suffix)
            previous.append((setter,key,getter(key)));setter(key,value)
            require(abs(getter(key)-value)<1e-10,'Cannot set export preference')
        for name,sources in JOBS.items():
            if args.only and name not in args.only:continue
            native=TARGET/'solidworks'/(name+'.SLDPRT')
            if not native.exists():
                copies=[]
                for filename,body_name in sources:
                    source=reopen(sw,SOURCE/(filename+'.SLDPRT'))
                    body=next(interface(b,'IBody2') for b in interface(source,'IPartDoc').GetBodies2(0,False) if interface(b,'IBody2').Name==body_name)
                    copies.append((body_name,interface(body.Copy(),'IBody2')))
                    sw.CloseDoc(source.GetTitle())
                doc=new_document(sw)
                for body_name,body in copies:
                    f=interface(interface(doc,'IPartDoc').CreateFeatureFromBody3(body,False,1),'IFeature')
                    require(f,'Cannot copy source solid').Name='Source_'+body_name
                    current=interface(interface(doc,'IPartDoc').GetBodies2(0,False)[-1],'IBody2')
                    # Identify the imported body by its feature rather than body-list order.
                    faces=f.GetFaces()
                    current=interface(interface(faces[0],'IFace2').GetBody(),'IBody2')
                    current.Name=body_name
                    if 'fixing_head' in body_name:
                        move_body(doc,current,'Seat_'+body_name,z=-.30)
                    if body_name=='dimmer_cap':
                        # Close the source's 0.000804 mm axial gap for one printable solid.
                        move_body(doc,current,'Seat_Dimmer_Cap',z=-.002)
                doc.ClearSelection2(True)
                sd=interface(doc.SelectionManager,'ISelectionMgr').CreateSelectData();sd.Mark=2
                for i,b in enumerate(interface(doc,'IPartDoc').GetBodies2(0,False)):
                    require(interface(b,'IBody2').Select2(i>0,sd),'Cannot select combine body')
                f=doc.FeatureManager.InsertCombineFeature(15903,None,None)
                require(f,'Print union failed').Name='Union_For_Print'
                checked(doc)
                save_new(sw,doc,native)
                sw.CloseDoc(doc.GetTitle())
            doc=reopen(sw,native)
            geometry=checked(doc)
            step=TARGET/'step'/(name+'.step');stl=TARGET/'stl'/(name+'.stl')
            for path in (step,stl):
                if not path.exists():save_new(sw,doc,path)
            for actual in stl.parent.iterdir():
                if actual.name.lower()==stl.name and actual.name!=stl.name:actual.rename(stl)
            mesh=check_stl(stl,geometry)
            mesh.update(mesh_topology(stl))
            close_session(sw,False)
            require('AUTOMOTIVE_DESIGN' in step.read_text(errors='replace')[:5000],'Expected AP214')
            try:
                imported,error=sw.LoadFile4(str(step),'',sw.GetImportFileData(str(step)),0)
                require(imported and error==0,'STEP import failed')
                actual=solid_geometry(interface(imported,'IModelDoc2'))
                require(actual['solid_count']==1,'STEP must contain one solid')
                require(abs(actual['volume_mm3']/geometry['volume_mm3']-1)<1e-4,'STEP volume differs')
                require(max(abs(a-b) for a,b in zip(actual['bounds_mm'],geometry['bounds_mm']))<.002,'STEP bounds differ')
            finally:
                sw.CloseAllDocuments(True)
            report['items'][name]={'native':str(native),'source_bodies':sources,'reopened':True,'geometry':geometry,'stl':mesh,'step_reimported_solids':1}
            if name=='1gang_print_dimmer':report['items'][name]['cap_translation_z_mm']=-.002
            report_path.parent.mkdir(parents=True,exist_ok=True)
            report_path.write_text(json.dumps(report,indent=2))
            print('VALIDATED PRINT ITEM',name,flush=True)
    finally:
        for setter,key,value in reversed(previous):setter(key,value)
        close_session(sw)
        require(hashes()==baseline,'Source version changed')


if __name__=='__main__':main()
