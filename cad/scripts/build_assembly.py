"""Build the two static, natively mated Latoun 004 design-review assemblies."""
import argparse
import json
import math
import faulthandler
from sw_helpers import *


def transform(sw, angle=0, y=0, z=0):
    a=math.radians(angle)
    c,s=math.cos(a),math.sin(a)
    values=[1.,0.,0., 0.,c,s, 0.,-s,c, 0.,y/1000,z/1000, 1.,0.,0.,0.]
    utility=interface(sw.GetMathUtility(),'IMathUtility')
    return interface(utility.CreateTransform(com.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,values)),'IMathTransform')


def mate_features(model):
    group=interface(interface(model,'IAssemblyDoc').FeatureByName('Mates'),'IFeature')
    if not group:
        root=interface(model.FirstFeature(),'IFeature')
        while root:
            if root.GetTypeName2()=='MateGroup':
                group=root
                break
            root=interface(root.GetNextFeature(),'IFeature')
    if not group:
        return []
    result=[]
    item=interface(group.GetFirstSubFeature(),'IFeature')
    while item:
        result.append(item)
        item=interface(item.GetNextSubFeature(),'IFeature')
    return result


def lock_mate(model, a, b, name):
    existing={f.Name for f in mate_features(model)}
    assembly=interface(model,'IAssemblyDoc')
    model.ClearSelection2(True)
    sd=interface(model.SelectionManager,'ISelectionMgr').CreateSelectData()
    sd.Mark=1
    require(a.Select4(False,sd,False),'Reference component selection failed')
    require(b.Select4(True,sd,False),'Component selection failed')
    mate,error=assembly.AddMate5(16,0,False,0.,0.,0.,0.,0.,0.,0.,0.,False,False,0,0)
    require(mate and error==1,f'Lock mate {name} failed: {error}')
    new=[f for f in mate_features(model) if f.Name not in existing]
    require(len(new)==1,f'Cannot identify newly added mate {name}')
    new[0].Name=name
    model.ClearSelection2(True)
    return name


def inspect_assembly(model, expected, expected_mates):
    require(model.EditRebuild3(),'Assembly rebuild failed')
    assembly=interface(model,'IAssemblyDoc')
    components=[interface(c,'IComponent2') for c in assembly.GetComponents(False)]
    require(len(components)==len(expected),'Component count mismatch')
    rows=[]
    for c in components:
        path=Path(c.GetPathName())
        require(path.exists(),'Missing component '+str(path))
        require(c.GetSuppression2()==2,'Component is not fully resolved: '+c.Name2)
        require(c.GetModelDoc2(),'Missing loaded part: '+c.Name2)
        arr=list(c.Transform2.ArrayData)
        rows.append({'instance':c.Name2,'path':str(path),'fixed':c.IsFixed(),'transform':arr})
        key=c.Name2
        require(key in expected,'Unexpected instance '+key)
        require(max(abs(a-b) for a,b in zip(arr,expected[key]))<1e-7,'Component moved: '+key)
    require(sum(r['fixed'] for r in rows)==1,'Expected exactly one grounded component')
    mates=[]
    for f in mate_features(model):
        if f.Name not in expected_mates:
            continue
        error,warning=f.GetErrorCode2()
        require(error==0,f'Mate {f.Name} error {error}')
        mates.append({'name':f.Name,'type':f.GetTypeName2(),'error':error,'warning':warning})
    require(len(mates)==len(expected_mates),'Mate count mismatch')
    manager=assembly.InterferenceDetectionManager
    manager.TreatCoincidenceAsInterference=False
    manager.IncludeMultibodyPartInterferences=False
    manager.MakeInterferingPartsTransparent=False
    overlaps=[]
    for item in manager.GetInterferences() or []:
        hit=interface(item,'IInterference')
        overlaps.append({'components':[interface(c,'IComponent2').Name2 for c in hit.Components],
                         'volume_mm3':hit.Volume*1e9,'possible_only':hit.IsPossibleInterference})
    manager.Done()
    return {'components':rows,'mates':mates,'interferences_preserved':overlaps,'rebuild_ok':True}


def build(sw,variant):
    name='Latoun_'+variant+'_004'
    path=OUT/(name+'.SLDASM')
    require(not path.exists(),'Refusing to overwrite '+str(path))
    parts=[('Common_Plate',0,0,0),('Rear_Ring',0,0,0),
           ('Fixing_Head',0,-41.5,0),('Fixing_Head',0,41.5,0)]
    if variant=='Toggle':
        parts += [('Switch_Insert',0,0,0),('Switch_Bezel',0,0,0),
                  ('Switch_Stem',25,0,-10),('Switch_Grip',25,0,-10)]
    else:
        parts += [(p,0,0,0) for p in ['Dimmer_Insert','Dimmer_Base','Dimmer_Collar','Dimmer_Grip','Dimmer_Cap']]
    for part,_,_,_ in parts:
        require((OUT/(part+'_004.SLDPRT')).exists(),'Part missing: '+part)
    # AddComponent5 requires the source parts to be loaded in memory.
    loaded={p:reopen(sw,OUT/(p+'_004.SLDPRT')) for p in dict.fromkeys(t[0] for t in parts)}
    model=new_document(sw,2)
    assembly=interface(model,'IAssemblyDoc')
    model.AddCustomInfo3('','Revision',30,'004')
    model.AddCustomInfo3('','Purpose',30,'Early appearance and quotation review; not a mechanism or manufacturing release')
    model.AddCustomInfo3('','Pose',30,'Static rigid review mates; actuator pivot Z=-10 mm, angle +25 deg')
    expected={}
    mates=[]
    primary=None
    stem=None
    for part,angle,y,z in parts:
        component=assembly.AddComponent5(str(OUT/(part+'_004.SLDPRT')),0,'',False,'',0.,0.,0.)
        require(component,'Component insertion failed: '+part)
        component.Transform2=transform(sw,angle,y,z)
        expected[component.Name2]=list(component.Transform2.ArrayData)
        if primary is None:
            component.Select4(False,None,False)
            assembly.FixComponent()
            primary=component
        else:
            anchor=stem if part=='Switch_Grip' else primary
            mates.append(lock_mate(model,anchor,component,'Review_Position_'+component.Name2.replace('-','_')))
        if part=='Switch_Stem':
            stem=component
        print('  MATED',component.Name2,flush=True)
    if variant=='Toggle':
        equations=model.GetEquationMgr()
        # Named reference values document the study; rigid mates preserve the
        # shown pose. They are deliberately not advertised as a mechanism.
        for eq in ['"Reference_Pivot_Z" = -10mm','"Reference_Pose" = 25deg',
                   '"Reference_Travel_Min" = -25deg','"Reference_Travel_Max" = 25deg']:
            require(equations.Add2(-1,eq,True)>=0,'Reference variable creation failed')
    result=inspect_assembly(model,expected,mates)
    result['save']=save_new(sw,model,path,2)
    sw.CloseDoc(model.GetTitle())
    model=reopen(sw,path,2)
    result['reopened']=inspect_assembly(model,expected,mates)
    result['path']=str(path)
    (OUT/(name+'_validation.json')).write_text(json.dumps(result,indent=2))
    model.ShowNamedView2('*Isometric',7)
    model.ViewZoomtofit2()
    preview=OUT/(name+'_isometric.bmp')
    require(model.SaveBMP(str(preview),1600,1200),'Preview capture failed')
    print('VALIDATED ASSEMBLY',path.name,flush=True)
    return model


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',choices=['Toggle','Dimmer'])
    args=parser.parse_args()
    sw=connect()
    faulthandler.dump_traceback_later(300,repeat=True)
    try:
        for variant in [args.only] if args.only else ['Toggle','Dimmer']:
            build(sw,variant)
    finally:
        # Restore the user's pre-test input-dimension preference from the initial session.
        sw.SetUserPreferenceToggle(10,True)
        faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':
    main()
