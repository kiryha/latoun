"""Check saved revision 004 solids, export AP214, and reopen the exports."""
import argparse
import json
import math
import faulthandler
from sw_helpers import *


def validate_parts(sw):
    manifest=json.loads((OUT/'parts_validation.json').read_text())
    envelopes={'Common_Plate':[70,120,3],'Rear_Ring':[66,116,2],
        'Fixing_Head':[8,7,3],'Switch_Insert':[38,74,3],
        'Switch_Bezel':[22,50,4],'Switch_Stem':[4,10,23],
        'Switch_Grip':[10,10,20],'Dimmer_Insert':[38,74,3],
        'Dimmer_Base':[24,24,4],'Dimmer_Collar':[14,14,5],
        'Dimmer_Grip':[16,16,20],'Dimmer_Cap':[15,15,1.3]}
    report={}
    for name,record in manifest.items():
        doc=reopen(sw,Path(record['path']))
        result=part_check(doc,[f['name'] for f in record['features']])
        bounds=result['bounds_mm']
        size=[bounds[i+3]-bounds[i] for i in range(3)]
        error=max(abs(a-b) for a,b in zip(size,envelopes[name]))
        require(error<.002,f'Envelope mismatch {name}: {size}')
        result['envelope_mm']=size
        result['envelope_error_mm']=error
        if name=='Dimmer_Grip':
            body=interface(interface(doc,'IPartDoc').GetBodies2(0,False)[0],'IBody2')
            faces=[interface(f,'IFace2') for f in body.GetFaces()]
            samples=[]
            for z in [10,11,17,23,26]:
                phase=math.radians((z-8)*2.25)
                for theta in [0,.033,.079,.127]:
                    radius=7.75+.25*math.cos(40*(theta-phase))
                    p=[radius*math.cos(theta)/1000,radius*math.sin(theta)/1000,z/1000]
                    distances=[]
                    for face in faces:
                        q=face.GetClosestPointOn(*p)
                        if q:
                            distances.append(math.dist(p,q[:3])*1000)
                    samples.append({'z_mm':z,'theta_rad':theta,'distance_mm':min(distances)})
            result['cosine_surface_samples']=samples
            result['max_cosine_surface_error_mm']=max(s['distance_mm'] for s in samples)
            require(result['max_cosine_surface_error_mm']<.005,'Flute phase/profile mismatch')
        report[name]=result
        print('CHECKED',name,size,flush=True)
    (OUT/'final_geometry_validation.json').write_text(json.dumps(report,indent=2))
    return report


def imported_solids(doc):
    if doc.GetType()==1:
        bodies=interface(doc,'IPartDoc').GetBodies2(0,False) or []
        volumes=[]
        for b in bodies:
            body=interface(b,'IBody2')
            require(body.Check()==1,'Invalid imported solid')
            volumes.append(body.GetMassProperties(1.)[3]*1e9)
        return volumes
    volumes=[]
    for c in interface(doc,'IAssemblyDoc').GetComponents(False) or []:
        part=interface(interface(c,'IComponent2').GetModelDoc2(),'IModelDoc2')
        require(part,'Unresolved imported component')
        if part.GetType()==1:
            volumes.extend(imported_solids(part))
    return volumes


def exports(sw,geometry):
    target=ROOT/'output'/'step'/'004'
    target.mkdir(parents=True,exist_ok=True)
    jobs=[(OUT/(n+'_004.SLDPRT'),1,[v['volume_mm3']]) for n,v in geometry.items()]
    for variant in ['Toggle','Dimmer']:
        name='Latoun_'+variant+'_004'
        report=json.loads((OUT/(name+'_validation.json')).read_text())
        volumes=[geometry[Path(c['path']).stem.removesuffix('_004')]['volume_mm3']
                 for c in report['reopened']['components']]
        jobs.append((OUT/(name+'.SLDASM'),2,volumes))
    old_ap=sw.GetUserPreferenceIntegerValue(75)
    results={}
    try:
        require(sw.SetUserPreferenceIntegerValue(75,214),'Cannot set STEP AP214')
        for native,kind,expected in jobs:
            step=target/(native.stem+'.step')
            if step.exists():
                print('Preserving and validating existing STEP',step.name,flush=True)
                saved={'preserved_existing':True}
            else:
                doc=reopen(sw,native,kind)
                activated,error=sw.ActivateDoc3(doc.GetTitle(),False,0,0)
                require(activated and error==0,'Cannot activate export document')
                saved=save_new(sw,doc,step,kind)
            require('AUTOMOTIVE_DESIGN' in step.read_text(errors='replace')[:5000],'STEP is not AP214')
            data=sw.GetImportFileData(str(step))
            imported,error=sw.LoadFile4(str(step),'',data,0)
            require(imported and error==0,f'STEP reopen failed: {error}')
            imported=interface(imported,'IModelDoc2')
            actual=imported_solids(imported)
            require(len(actual)==len(expected),f'STEP solid count {len(actual)} != {len(expected)}')
            relative=abs(sum(actual)-sum(expected))/sum(expected)
            # Loft integration can differ slightly after translation. This is
            # a 0.01% numerical volume check, not a manufacturing tolerance.
            require(relative<1e-4,f'STEP volume mismatch: {relative}')
            envelope_error=None
            if kind==1:
                check=part_check(imported,[])
                original=geometry[native.stem.removesuffix('_004')]['bounds_mm']
                envelope_error=max(abs(a-b) for a,b in zip(check['bounds_mm'],original))
                require(envelope_error<.002,'STEP envelope mismatch')
            results[native.stem]={'path':str(step),'schema':'AP214','save':saved,
                'reopened':True,'valid_solids':len(actual),'volume_mm3':sum(actual),
                'relative_volume_difference':relative,'envelope_error_mm':envelope_error}
            (target/'step_validation.json').write_text(json.dumps(results,indent=2))
            sw.CloseDoc(imported.GetTitle())
            print('VALIDATED STEP',step.name,flush=True)
    finally:
        sw.SetUserPreferenceIntegerValue(75,old_ap)
    # Leave the two native review assemblies available in the SOLIDWORKS UI.
    for variant in ['Dimmer','Toggle']:
        doc=reopen(sw,OUT/f'Latoun_{variant}_004.SLDASM',2)
        sw.ActivateDoc3(doc.GetTitle(),False,0,0)
        doc.ShowNamedView2('*Isometric',7)
        doc.ViewZoomtofit2()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--geometry-only',action='store_true')
    parser.add_argument('--export-only',action='store_true')
    args=parser.parse_args()
    sw=connect()
    faulthandler.dump_traceback_later(300,repeat=True)
    geometry=json.loads((OUT/'final_geometry_validation.json').read_text()) if args.export_only else validate_parts(sw)
    if not args.geometry_only:
        exports(sw,geometry)
    faulthandler.cancel_dump_traceback_later()
