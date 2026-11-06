"""Build the two static, natively mated Latoun design-review assemblies."""
import argparse
import json
import math
import faulthandler
from sw_helpers import *
from model_layout import ASSEMBLIES, ASSETS, check_manifest, instances, leaf_instances, native_filename, pose_values


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


def inspect_assembly(model, name):
    require(model.EditRebuild3(),'Assembly rebuild failed')
    assembly=interface(model,'IAssemblyDoc')
    top=[interface(c,'IComponent2') for c in assembly.GetComponents(True) or []]
    expected={instance:(child,pose_values(a,y,z)) for instance,child,a,y,z in instances(name)}
    require(len(top)==len(expected),'Top-level component count mismatch')
    rows=[]
    for c in top:
        require(c.Name2 in expected,'Unexpected component '+c.Name2)
        child,pose=expected[c.Name2]
        path=Path(c.GetPathName())
        require(path==OUT/native_filename(child) and path.exists(),'Incorrect component reference: '+str(path))
        require(c.GetSuppression2()==2 and c.GetModelDoc2(),'Unresolved component '+c.Name2)
        actual=list(c.Transform2.ArrayData)
        require(max(abs(a-b) for a,b in zip(actual,pose))<1e-7,'Component moved: '+c.Name2)
        rows.append({'instance':c.Name2,'path':str(path),'fixed':c.IsFixed(),'transform':actual})
    require(sum(c['fixed'] for c in rows)==1,'Expected one fixed reference component')
    expected_leaves={instance:(child,pose) for instance,child,pose in leaf_instances(name)}
    leaves=[]
    for obj in assembly.GetComponents(False) or []:
        c=interface(obj,'IComponent2')
        loaded=interface(c.GetModelDoc2(),'IModelDoc2')
        require(loaded,'Unresolved descendant '+c.Name2)
        if loaded.GetType()!=1:
            continue
        require(c.Name2 in expected_leaves,'Unexpected leaf '+c.Name2)
        child,pose=expected_leaves[c.Name2]
        actual=list(c.GetTotalTransform(False).ArrayData)
        require(Path(c.GetPathName())==OUT/native_filename(child),'Incorrect leaf reference')
        require(max(abs(a-b) for a,b in zip(actual,pose))<1e-7,'Leaf moved: '+c.Name2)
        leaves.append({'instance':c.Name2,'part':child,'path':c.GetPathName(),'transform':actual})
    require(len(leaves)==len(expected_leaves),'Leaf count mismatch')
    mates=[]
    for f in mate_features(model):
        if not f.Name.startswith('position_'):
            continue
        error,warning=f.GetErrorCode2()
        require(error==0,'Mate failure: '+f.Name)
        mates.append({'name':f.Name,'type':f.GetTypeName2(),'error':error,'warning':warning})
    require(len(mates)==len(top)-1,'Mate count mismatch')
    manager=assembly.InterferenceDetectionManager
    manager.TreatCoincidenceAsInterference=False
    manager.IncludeMultibodyPartInterferences=True
    manager.TreatSubAssembliesAsComponents=False
    manager.MakeInterferingPartsTransparent=False
    overlaps=[]
    try:
        for obj in manager.GetInterferences() or []:
            hit=interface(obj,'IInterference')
            overlaps.append({'components':[interface(c,'IComponent2').Name2 for c in hit.Components],
                             'volume_mm3':hit.Volume*1e9,'possible_only':hit.IsPossibleInterference})
    finally:
        manager.Done()
    return {'rebuild_ok':True,'components':rows,'leaves':leaves,'mates':mates,
            'geometry':solid_geometry(model),'interferences_preserved':overlaps}


def build(sw,name):
    path=OUT/native_filename(name)
    require(not path.exists(),'Refusing to overwrite '+str(path))
    for _,child,_,_,_ in instances(name):
        reopen(sw,OUT/native_filename(child),2 if child in ASSEMBLIES else 1)
    model=new_document(sw,2)
    assembly=interface(model,'IAssemblyDoc')
    model.AddCustomInfo3('','Purpose',30,'Early appearance and quotation review; static assembly')
    if name in ASSETS:
        model.AddCustomInfo3('','Latoun_Asset_ID',30,ASSETS[name])
    primary=None
    for instance,child,angle,y,z in instances(name):
        c=assembly.AddComponent5(str(OUT/native_filename(child)),0,'',False,'',0.,0.,0.)
        require(c,'Component insertion failed: '+child)
        if c.IsFixed():
            c.Select4(False,None,False)
            assembly.UnfixComponent()
        c.Transform2=transform(sw,angle,y,z)
        require(c.Name2==instance,'Unexpected instance numbering')
        if primary is None:
            c.Select4(False,None,False)
            assembly.FixComponent()
            primary=c
        else:
            lock_mate(model,primary,c,'position_'+instance.replace('-','_'))
        print('  MATED',instance,flush=True)
    model.ClearSelection2(True)
    checked=inspect_assembly(model,name)
    saved=save_new(sw,model,path,2)
    sw.CloseDoc(model.GetTitle())
    model=reopen(sw,path,2)
    checked=inspect_assembly(model,name)
    previous=VALIDATION/(name+'_validation.json')
    if previous.exists():
        old=json.loads(previous.read_text())['reopened']['geometry']
        actual=checked['geometry']
        require(old['solid_count']==actual['solid_count'],'Product solid count changed')
        require(max(abs(a-b) for a,b in zip(old['bounds_mm'],actual['bounds_mm']))<.002,'Product bounds changed')
        require(all(abs(a-b)/a<1e-5 for a,b in zip(old['solid_volumes_mm3'],actual['solid_volumes_mm3'])),'Product solid volumes changed')
    write_report(name+'_validation.json',{'path':str(path),'asset_id':ASSETS.get(name),'save':saved,'reopened':checked})
    print('VALIDATED ASSEMBLY',name,flush=True)
    return model


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='+',choices=list(ASSEMBLIES))
    args=parser.parse_args()
    check_manifest()
    sw=connect()
    faulthandler.dump_traceback_later(300,repeat=True)
    try:
        for name in args.only or ASSEMBLIES:
            path=OUT/native_filename(name)
            if path.exists():
                require((VALIDATION/(name+'_validation.json')).exists(),'Existing untracked assembly: '+name)
                doc=reopen(sw,path,2)
                checked=inspect_assembly(doc,name)
                record=json.loads((VALIDATION/(name+'_validation.json')).read_text())
                record['reopened']=checked
                write_report(name+'_validation.json',record)
                print('PRESERVED AND CHECKED',name,flush=True)
            else:
                build(sw,name)
            close_session(sw,exit_app=False)
    finally:
        faulthandler.cancel_dump_traceback_later()
        close_session(sw)


if __name__=='__main__':
    main()
