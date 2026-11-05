"""Build native Latoun appearance parts. No existing design is overwritten."""
import argparse
import faulthandler
import json
import math
from pathlib import Path
from sw_helpers import *
from profiles import simplified_loop


def insert(doc,switch=False):
    a=rr_sketch(doc,'Rear_38x74_R8',0,38,74,8)
    b=rr_sketch(doc,'Face_34x70_R6',3,34,70,6)
    loft(doc,[a,b],'Insert_Taper')
    names=['Insert_Taper']
    if switch:
        a=rr_sketch(doc,'Slot_Rear_5x22',0,5,22,.5)
        b=rr_sketch(doc,'Slot_Front_5x25',3,5,25,.5)
        loft(doc,[a,b],'Actuator_Opening',True)
        names+=['Actuator_Opening']
    return names


def plate(doc):
    stations=[(0,69.5,119.5,3),(.25,70,120,3),(2.75,65.5,115.5,2.5),(3,65,115,2.5)]
    sketches=[rr_sketch(doc,f'Outline_{i}',*st) for i,st in enumerate(stations)]
    names=[]
    for i in range(3):
        name=['Rear_Edge_Break','Main_Edge_Taper','Front_Edge_Break'][i]
        loft(doc,sketches[i:i+2],name)
        names.append(name)
    a=rr_sketch(doc,'Window_Rear',0,38.5,74.5,8.25)
    b=rr_sketch(doc,'Window_Front',3,34.5,70.5,6.25)
    loft(doc,[a,b],'Insert_Window_Reveal_025',True)
    names+=['Insert_Window_Reveal_025']
    # Two holes share one dimensioned sketch and a single native extruded cut.
    sm=start_sketch(doc,'Fixings_D3_83_Pitch',3)
    sk=finish_sketch(doc,'Fixings_D3_83_Pitch',[circle(sm,3,0,41.5),circle(sm,3,0,-41.5)])
    cut_extrude(doc,sk,3,'Fixing_Holes_D3_83_Pitch')
    return names+['Fixing_Holes_D3_83_Pitch']


def ring(doc):
    sm=start_sketch(doc,'Ring_66x116_Wall2',-2)
    sk=finish_sketch(doc,'Ring_66x116_Wall2',rounded_rect(sm,66,116,1)+rounded_rect(sm,62,112,1))
    extrude(doc,sk,2,'Ring_Thickness_2')
    return ['Ring_Thickness_2']


def bezel(doc):
    a=rr_sketch(doc,'Bezel_Rear_22x50_R7',3,22,50,7)
    b=rr_sketch(doc,'Bezel_Front_16x44_R4',7,16,44,4)
    loft(doc,[a,b],'Bezel_Taper')
    a=rr_sketch(doc,'Slot_Joint_5x25',3,5,25,.5)
    b=rr_sketch(doc,'Slot_Front_5x29',7,5,29,.5)
    loft(doc,[a,b],'Bezel_Actuator_Opening',True)
    return ['Bezel_Taper','Bezel_Actuator_Opening']


def base(doc):
    revolve(doc,'Turned_Base_D24_D17',[(3,0),(3,12),(7,8.5),(7,0)])
    return ['Turned_Base_D24_D17']


def collar(doc):
    revolve(doc,'Turned_Collar_D14',[(6,0),(6,7),(11,7),(11,0)])
    return ['Turned_Collar_D14']


def cap(doc):
    revolve(doc,'Turned_Cap_D15_D14',[(28,0),(28,7.5),(29,7),(29,0)])
    p=simplified_loop('raised_L/Z29.001')
    lo=[min(v[i] for v in p) for i in (0,1)]
    hi=[max(v[i] for v in p) for i in (0,1)]
    p=[tuple((v[i]-(lo[i]+hi[i])/2)*7/(hi[i]-lo[i]) for i in (0,1)) for v in p]
    sm=start_sketch(doc,'Raised_L_7x7_Outline',29)
    # This decorative traced outline is fixed as a group, while its boss height
    # remains a native driving parameter. Fine source bevels are omitted.
    ents=polygon(sm,p)
    doc.ClearSelection2(True)
    for i,e in enumerate(ents): e.Select4(i!=0,None)
    doc.SketchAddConstraints('sgFIXED')
    sk=finish_sketch(doc,'Raised_L_7x7_Outline',ents,False)
    extrude(doc,sk,.3,'Raised_L_030')
    return ['Turned_Cap_D15_D14','Raised_L_030']


def stem(doc):
    sk=rr_sketch(doc,'Stem_4x10_R05',-2,4,10,.5)
    extrude(doc,sk,23,'Stem_Length_23')
    sm=start_sketch(doc,'Reference_Pivot_D1',0,'Right Plane')
    sk=finish_sketch(doc,'Reference_Pivot_D1',[circle(sm,1)])
    cut_extrude(doc,sk,3,'Reference_Pivot_Bore',True)
    return ['Stem_Length_23','Reference_Pivot_Bore']


def grip(doc):
    sk=rr_sketch(doc,'Grip_10x10_R16',20,10,10,1.6)
    extrude(doc,sk,20,'Grip_Blank_Length20')
    sm=start_sketch(doc,'Curved_Ends_R10',0,'Right Plane')
    ents=polygon(sm,[(-45,-15),(-15,-15),(-15,15),(-45,15)])+[circle(sm,20,-30,0)]
    sk=finish_sketch(doc,'Curved_Ends_R10',ents)
    cut_extrude(doc,sk,6,'Sculpted_Cylindrical_End_Cuts',True)
    return ['Grip_Blank_Length20','Sculpted_Cylindrical_End_Cuts']


def flute_profile(doc,name,z,mean_radius=7.75):
    sm=start_sketch(doc,name,z)
    phase=math.radians(2.25*(z-8))
    entities=[]
    # Forty smooth B-spline segments sample the supplied cosine equation at 13
    # points per period. This produces native curved faces, not mesh triangles.
    for k in range(40):
        points=[]
        for j in range(13):
            t=(k+j/12)*2*math.pi/40
            radius=mean_radius+.25*math.cos(40*t)
            points.extend([radius*math.cos(t+phase)/1000,radius*math.sin(t+phase)/1000,0.])
        arr=com.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,points)
        entities.append(require(sm.CreateSpline2(arr,False),'Cosine spline failed'))
    doc.ClearSelection2(True)
    for i,e in enumerate(entities):e.Select4(i!=0,None)
    doc.SketchAddConstraints('sgFIXED')
    return finish_sketch(doc,name,entities,False)


def fluted_body(doc):
    profile=flute_profile(doc,'Cosine_40_Flute_Profile',8.2)
    # A straight 3D path plus a prescribed twist creates a true native sweep.
    doc.ClearSelection2(True)
    doc.Insert3DSketch2(True)
    path_line=doc.SketchManager.CreateLine(0.,0.,.0082,0.,0.,.0278)
    doc.ClearSelection2(True)
    path_line.Select4(False,None)
    doc.SketchAddConstraints('sgFIXED')
    doc.Insert3DSketch2(True)
    path=interface(doc.FeatureByPositionReverse(0),'IFeature')
    path.Name='Helix_Axis_Length19_6'
    doc.ClearSelection2(True)
    profile.Select2(False,1)
    path.Select2(True,4)
    sweep=doc.FeatureManager.InsertProtrusionSwept4(False,False,8,True,False,
        0,0,False,0.,0.,0,0,True,True,True,math.radians(44.1),True,False,0.,0)
    require(sweep,'Twisted cosine sweep failed').Name='Helical_Grip_Lead160'
    # Thin end lofts reduce the whole radial profile by .2, as in sheet 08.
    lower=flute_profile(doc,'Lower_End_Reduced02',8,7.55)
    loft(doc,[lower,profile],'Lower_End_Break_02')
    upper=flute_profile(doc,'Upper_Working_Profile',27.8)
    end=flute_profile(doc,'Upper_End_Reduced02',28,7.55)
    loft(doc,[upper,end],'Upper_End_Break_02')
    return ['Helical_Grip_Lead160','Lower_End_Break_02','Upper_End_Break_02']


def head(doc):
    sketches=[]
    for i,(z,w,h) in enumerate([(3,7.8,6.8),(3.1,8,7),(5.5,8,7),(6,7,6)]):
        name=f'Hex_Station_{i}'
        sm=start_sketch(doc,name,z)
        points=[(w/2,0),(w/4,h/2),(-w/4,h/2),(-w/2,0),(-w/4,-h/2),(w/4,-h/2)]
        sketches.append(finish_sketch(doc,name,polygon(sm,points)))
    names=[]
    for i in range(3):
        name=['Head_Lower_Break','Head_Blank','Head_Upper_Bevel'][i]
        loft(doc,sketches[i:i+2],name)
        names.append(name)
    cross=[(-.5,-2),(.5,-2),(.5,-.5),(2,-.5),(2,.5),(.5,.5),(.5,2),(-.5,2),(-.5,.5),(-2,.5),(-2,-.5),(-.5,-.5)]
    sketches=[]
    for z in (5,6):
        name=f'Cross_Recess_Z{z}'
        sm=start_sketch(doc,name,z)
        sketches.append(finish_sketch(doc,name,polygon(sm,cross)))
    loft(doc,sketches,'Decorative_Cross_Recess_1_Deep',True)
    return names+['Decorative_Cross_Recess_1_Deep']


JOBS={'1gang_plate':plate,'1gang_rear_ring':ring,'plate_fixing_head':head,
      'switch_insert':lambda d:insert(d,True),'switch_bezel':bezel,
      'dimmer_insert':insert,'dimmer_base':base,'dimmer_collar':collar,'dimmer_cap':cap,
      'switch_stem':stem,'switch_grip':grip,'dimmer_grip':fluted_body}


def main():
    args=argparse.ArgumentParser()
    args.add_argument('--only',nargs='*')
    opt=args.parse_args()
    sw=connect()
    old_prompt=sw.GetUserPreferenceToggle(10)
    sw.SetUserPreferenceToggle(10,False)
    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'parts_validation.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    faulthandler.dump_traceback_later(300,repeat=True)
    current=None
    try:
        for name in opt.only or JOBS:
            path=OUT/(name+'.SLDPRT')
            if path.exists():
                require(name in manifest,'Existing untracked file; refusing to overwrite '+str(path))
                print('Already saved; preserving',path.name,flush=True)
                continue
            print('BUILD',name,flush=True)
            current=new_document(sw)
            current.AddCustomInfo3('','Design_Status',30,'Early appearance / quotation model; unresolved interfaces preserved')
            names=JOBS[name](current)
            result=part_check(current,names)
            result['save']=save_new(sw,current,path)
            sw.CloseDoc(current.GetTitle())
            current=reopen(sw,path)
            result['reopened']=part_check(current,names)
            result['path']=str(path)
            manifest[name]=result
            manifest_path.write_text(json.dumps(manifest,indent=2))
            sw.CloseDoc(current.GetTitle())
            current=None
            print('VALIDATED',name,result['bounds_mm'],flush=True)
    finally:
        faulthandler.cancel_dump_traceback_later()
        if current is not None:
            sw.CloseDoc(current.GetTitle())
        sw.SetUserPreferenceToggle(10,old_prompt)
        close_session(sw)


if __name__=='__main__':
    main()
