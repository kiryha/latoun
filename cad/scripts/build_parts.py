"""Build native Latoun appearance parts. No existing design is overwritten."""
import argparse
import hashlib
import faulthandler
import json
import math
from sw_helpers import *
from profiles import input_loop, rdp
import sw_helpers
from model_layout import ASSETS, check_manifest


def soften_caps(doc,name,radius):
    doc.ClearSelection2(True)
    count=0
    for obj in sw_helpers.active_body.GetEdges():
        edge=interface(obj,'IEdge')
        values=edge.GetCurveParams2()
        if values and abs(values[2]-values[5])<1e-9:
            require(interface(edge,'IEntity').Select4(count>0,None),'Fillet edge selection failed')
            count+=1
    require(count,'No cap edges selected')
    f=doc.FeatureManager.FeatureFillet3(3,radius/1000,0.,0.,0,0,0,None,None,None,None,None,None,None)
    require(f,'Cap edge treatment failed: '+name).Name=name
    remember_body(doc)
    return name


def source_outline(doc,name,z,w,h,r,sx=1.,sy=1.):
    # Houdini point bevels are quadratic Beziers, not circular corner radii.
    sm=start_sketch(doc,name,z)
    entities=[]
    for x,y,angle in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        points=[]
        c,t=math.cos(math.radians(angle)),math.sin(math.radians(angle))
        for j in range(9):
            u=j/8
            px,py=r*(1-u*u),r*(2*u-u*u)
            points.extend([(x+c*px-t*py)*sx/1000,(y+t*px+c*py)*sy/1000,0.])
        entities.append(require(sm.CreateSpline2(com.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,points),False),'Corner spline failed'))
    for a,b in [((w/2,-h/2+r),(w/2,h/2-r)),((w/2-r,h/2),(-w/2+r,h/2)),((-w/2,h/2-r),(-w/2,-h/2+r)),((-w/2+r,-h/2),(w/2-r,-h/2))]:
        entities.append(line(sm,(a[0]*sx,a[1]*sy),(b[0]*sx,b[1]*sy)))
    doc.ClearSelection2(True)
    for i,e in enumerate(entities): e.Select4(i!=0,None)
    doc.SketchAddConstraints('sgFIXED')
    return finish_sketch(doc,name,entities,False)


def slot(doc,name):
    a=source_outline(doc,name+'_Rear',-.81,4.1,18.5,.4)
    b=source_outline(doc,name+'_Front',7.6,4.1,27.5,.4)
    loft(doc,[a,b],name,True)
    return name


def insert(doc,switch=False):
    a=source_outline(doc,'Insert_Rear_38x71',0,38,71,7.1)
    b=source_outline(doc,'Insert_Front_34x67',3,34,67,5.1)
    loft(doc,[a,b],'Insert_Taper')
    names=['Insert_Taper',soften_caps(doc,'Insert_Edge_Break',.15)]
    if switch: names.append(slot(doc,'Actuator_Opening'))
    return names


def plate(doc):
    a=source_outline(doc,'Plate_Rear_70x120',0,70,120,1)
    b=source_outline(doc,'Plate_Front_Scaled',3,70,120,1,.93,.962)
    loft(doc,[a,b],'Plate_Taper')
    a=source_outline(doc,'Window_Rear',0,38,71,7.1)
    b=source_outline(doc,'Window_Front',3,34,67,5.1)
    loft(doc,[a,b],'Insert_Window_Zero_Clearance',True)
    sm=start_sketch(doc,'Fixings_D3_83_Pitch',3)
    sk=finish_sketch(doc,'Fixings_D3_83_Pitch',[circle(sm,3,0,41.5),circle(sm,3,0,-41.5)])
    cut_extrude(doc,sk,3,'Fixing_Holes_D3_83_Pitch')
    return ['Plate_Taper','Insert_Window_Zero_Clearance','Fixing_Holes_D3_83_Pitch',soften_caps(doc,'Plate_Edge_Break',.15)]


def ring(doc):
    sm=start_sketch(doc,'Backing_Annulus',-2)
    sk=finish_sketch(doc,'Backing_Annulus',rounded_rect(sm,66,116,.159)+rounded_rect(sm,62.18,112.18,.159))
    extrude(doc,sk,2,'Backing_Thickness_2')
    return ['Backing_Thickness_2',soften_caps(doc,'Backing_Edge_Break',.159)]


def bezel(doc):
    a=source_outline(doc,'Collar_Rear',3,22.1,50.1,6.05)
    b=source_outline(doc,'Collar_Front',7,16,44,3)
    loft(doc,[a,b],'Collar_Taper')
    return ['Collar_Taper',soften_caps(doc,'Collar_Edge_Break',.1),slot(doc,'Collar_Opening')]


def base(doc):
    z=2.98164281845
    revolve(doc,'Turned_Base',[(z,0),(z,12),(z+4,8.6),(z+4,0)])
    return ['Turned_Base',soften_caps(doc,'Base_Edge_Break',.3)]


def collar(doc):
    z=6.12025104523
    revolve(doc,'Turned_Neck',[(z,0),(z,7),(z+5,7),(z+5,0)])
    return ['Turned_Neck']


def cap(doc):
    z=28.0012683868
    revolve(doc,'Turned_Cap',[(z-.4,0),(z-.4,7.5),(z+.4,7),(z+.4,0)])
    cap_edge=soften_caps(doc,'Cap_Edge_Break',.12)
    points=[(x*10+.364937484264,y*10) for x,y in input_loop('logo')]
    opposite=max(range(1,len(points)),key=lambda i:math.dist(points[0],points[i]))
    points=rdp(points[:opposite+1],.01)[:-1]+rdp(points[opposite:]+points[:1],.01)[:-1]
    sm=start_sketch(doc,'Logo_Outline',z+.373907905817)
    ents=polygon(sm,points)
    doc.ClearSelection2(True)
    for i,e in enumerate(ents):e.Select4(i!=0,None)
    doc.SketchAddConstraints('sgFIXED')
    sk=finish_sketch(doc,'Logo_Outline',ents,False)
    extrude(doc,sk,.3,'Raised_Logo')
    return ['Turned_Cap',cap_edge,'Raised_Logo']


def stem(doc):
    sk=rr_sketch(doc,'Stem_4x10',0,4,10,.5)
    extrude(doc,sk,23.4,'Stem_Length23_4')
    sm=start_sketch(doc,'Pivot_D1',0,'Right Plane')
    sk=finish_sketch(doc,'Pivot_D1',[circle(sm,1,-2,0)])
    cut_extrude(doc,sk,3,'Pivot_Bore',True)
    return ['Stem_Length23_4','Pivot_Bore']


def grip(doc):
    sk=rr_sketch(doc,'Grip_10x10',21.9161,10,10,1.6)
    extrude(doc,sk,20,'Grip_Blank')
    sm=start_sketch(doc,'Curved_Ends_R10',0,'Right Plane')
    ents=polygon(sm,[(-45,-15),(-15,-15),(-15,15),(-45,15)])+[circle(sm,20,-31.9161,0)]
    sk=finish_sketch(doc,'Curved_Ends_R10',ents)
    cut_extrude(doc,sk,6,'Sculpted_Ends',True)
    return ['Grip_Blank','Sculpted_Ends']


def fluted_body(doc):
    z=7.60046416521
    sm=start_sketch(doc,'Source_Flute_Section',z)
    points=input_loop('dimmer_flute_section')
    # Each period has two five-point bevel curves and two straight flanks.
    entities=[]
    require(len(points)==400,'Unexpected source flute section')
    for i in range(0,400,5):
        run=points[i:i+5]
        values=[v for x,y in run for v in (x/1000,y/1000,0.)]
        entities.append(require(sm.CreateSpline2(com.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,values),False),'Flute curve failed'))
        entities.append(line(sm,run[-1],points[(i+5)%400]))
    doc.ClearSelection2(True)
    for i,e in enumerate(entities):e.Select4(i!=0,None)
    doc.SketchAddConstraints('sgFIXED')
    profile=finish_sketch(doc,'Source_Flute_Section',entities,False)
    doc.ClearSelection2(True);doc.Insert3DSketch2(True)
    seg=doc.SketchManager.CreateLine(0.,0.,z/1000,0.,0.,(z+20)/1000)
    seg.Select4(False,None);doc.SketchAddConstraints('sgFIXED');doc.Insert3DSketch2(True)
    path=interface(doc.FeatureByPositionReverse(0),'IFeature');path.Name='Grip_Axis20'
    doc.ClearSelection2(True);profile.Select2(False,1);path.Select2(True,4)
    f=doc.FeatureManager.InsertProtrusionSwept4(False,False,8,True,False,0,0,False,0.,0.,0,0,False,True,True,math.radians(46),True,False,0.,0)
    require(f,'Source flute sweep failed').Name='Grip_Twist46'
    remember_body(doc)
    return ['Grip_Twist46']


def head(doc):
    z=3.28183
    h=4*math.sqrt(3)
    sketches=[]
    for i,(height,w) in enumerate([(0,8),(3-.643,8),(3,8-2*.643/math.cos(math.pi/6))]):
        sm=start_sketch(doc,f'Head_Section{i}',z+height)
        hh=w*math.sqrt(3)/2
        sketches.append(finish_sketch(doc,f'Head_Section{i}',polygon(sm,[(w/2,0),(w/4,hh/2),(-w/4,hh/2),(-w/2,0),(-w/4,-hh/2),(w/4,-hh/2)])))
    loft(doc,sketches[:2],'Head_Blank');loft(doc,sketches[1:],'Head_Top_Bevel')
    sm=start_sketch(doc,'Cross_Recess',z+3)
    a=.4;b=2
    p=[(-a,-b),(a,-b),(a,-a),(b,-a),(b,a),(a,a),(a,b),(-a,b),(-a,a),(-b,a),(-b,-a),(-a,-a)]
    sk=finish_sketch(doc,'Cross_Recess',polygon(sm,p))
    cut_extrude(doc,sk,3-2.11838495731,'Cross_Recess_Depth')
    return ['Head_Blank','Head_Top_Bevel','Cross_Recess_Depth']


JOBS={'1gang_plate_metal':plate,'1gang_plate_silicone':ring,'plate_fixing_head':head,
      'switch_insert':lambda d:insert(d,True),'switch_bezel':bezel,
      'dimmer_insert':insert,'dimmer_base':base,'dimmer_collar':collar,'dimmer_cap':cap,
      'switch_stem':stem,'switch_grip':grip,'dimmer_grip':fluted_body}


BODY_JOBS={
    '1gang_plate':['1gang_plate_metal','1gang_plate_silicone'],
    '1gang_plate_screws':['plate_fixing_head'],
    '1gang_slot1_switch':['switch_insert','switch_bezel','switch_stem','switch_grip'],
    '1gang_slot1_dimmer':['dimmer_insert','dimmer_base','dimmer_collar','dimmer_grip','dimmer_cap'],
}
BODY_COUNTS={'1gang_plate':2,'1gang_plate_screws':2,'1gang_slot1_switch':4,'1gang_slot1_dimmer':5}


def move_body(doc,body,name,y=0,z=0,angle=0,copy=False):
    doc.ClearSelection2(True)
    sd=interface(doc.SelectionManager,'ISelectionMgr').CreateSelectData()
    sd.Mark=1
    require(body.Select2(False,sd),'Move body selection failed')
    f=doc.FeatureManager.InsertMoveCopyBody2(0.,y/1000,z/1000,0.,0.,0.,0.,math.radians(angle),0.,0.,copy,1)
    require(f,'Move/copy body failed: '+name).Name=name
    if angle:
        # 2026 inserts these angles as Euler rotations; explicitly set Cartesian X.
        data=interface(f.GetDefinition(),'IMoveCopyBodyFeatureData')
        require(data.AccessSelections(doc,None),'Cannot edit body rotation')
        data.TransformX=math.radians(angle)
        data.TransformY=0.
        data.TransformZ=0.
        require(f.ModifyDefinition(data,doc,None),'Cannot set body X rotation')
    doc.ClearSelection2(True)
    return name


def check_asset(doc,name,names):
    require(doc.EditRebuild3(),'Part rebuild failed')
    result=solid_geometry(doc)
    require(result['solid_count']==BODY_COUNTS[name],'Incorrect body count: '+name)
    result['features']=[]
    for n in names:
        f=feature(doc,n)
        require(f,'Missing native feature '+n)
        error,warning=f.GetErrorCode2()
        require(error==0,'Feature rebuild error: '+n)
        result['features'].append({'name':n,'type':f.GetTypeName2(),'error':error,'warning':warning})
    result['body_names']=[interface(b,'IBody2').Name for b in interface(doc,'IPartDoc').GetBodies2(0,False)]
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='+',choices=list(ASSETS))
    opt=parser.parse_args()
    check_manifest()
    source_hash=hashlib.sha256((INPUT/'design.json').read_bytes()).hexdigest()
    report_path=VALIDATION/'parts_validation.json'
    records=json.loads(report_path.read_text()) if report_path.exists() else {}
    sw=connect()
    old_prompt=sw.GetUserPreferenceToggle(10)
    sw.SetUserPreferenceToggle(10,False)
    current=None
    try:
        for name in opt.only or ASSETS:
            path=OUT/(name+'.SLDPRT')
            if path.exists():
                require(name in records,'Existing untracked part '+name)
                require(records[name].get('input_sha256',source_hash)==source_hash,'Input changed; existing output must not be reused as current')
                current=reopen(sw,path)
                names=[f['name'] for f in records[name]['features']]
            else:
                print('BUILD',name,flush=True)
                current=new_document(sw)
                current.AddCustomInfo3('','Latoun_Asset_ID',30,ASSETS[name])
                names=[]
                for component in BODY_JOBS[name]:
                    begin_body(current)
                    names+=JOBS[component](current)
                    body=sw_helpers.active_body
                    body.Name=component
                    if component in ('switch_stem','switch_grip'):
                        names.append(move_body(current,body,component+'_Position',z=-12))
                    if component=='plate_fixing_head':
                        names.append(move_body(current,body,'Lower_Fixing_Position',y=-41.5))
                        body=interface(interface(current,'IPartDoc').GetBodies2(0,False)[0],'IBody2')
                        body.Name='lower_fixing_head'
                        names.append(move_body(current,body,'Second_Fixing_83_Pitch',y=83,copy=True))
                        for b in interface(current,'IPartDoc').GetBodies2(0,False):
                            b=interface(b,'IBody2')
                            b.Name='upper_fixing_head' if b.GetMassProperties(1.)[1]>0 else 'lower_fixing_head'
                check_asset(current,name,names)
                save_new(sw,current,path)
                sw.CloseDoc(current.GetTitle())
                current=reopen(sw,path)
            result=dict(records.get(name,{}))
            result.update(check_asset(current,name,names))
            # Structural changes must preserve the previously validated asset geometry.
            previous=VALIDATION/(name+'_validation.json')
            if previous.exists():
                old=json.loads(previous.read_text())['reopened']['geometry']
                require(max(abs(a-b) for a,b in zip(old['bounds_mm'],result['bounds_mm']))<.002,'Consolidation changed bounds')
                require(len(old['solid_volumes_mm3'])==result['solid_count'],'Consolidation changed body count')
                require(all(abs(a-b)/a<1e-5 for a,b in zip(old['solid_volumes_mm3'],result['solid_volumes_mm3'])),'Consolidation changed body volumes')
            result.update(path=str(path),reopened=True,asset_id=ASSETS[name],input_sha256=source_hash)
            records[name]=result
            write_report('parts_validation.json',records)
            sw.CloseDoc(current.GetTitle())
            current=None
            print('VALIDATED',name,result['solid_count'],'bodies',flush=True)
    finally:
        if current is not None:
            sw.CloseDoc(current.GetTitle())
        sw.SetUserPreferenceToggle(10,old_prompt)
        close_session(sw)


if __name__=='__main__':
    main()
