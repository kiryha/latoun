"""Export native parts as binary STL meshes for Houdini, in millimeters."""
import json
import struct
from sw_helpers import *


def check_stl(path,reference):
    data=path.read_bytes()
    require(len(data)>=84,'Truncated STL')
    count=struct.unpack_from('<I',data,80)[0]
    require(count>0 and len(data)==84+50*count,'Invalid binary STL size')
    low=[math.inf]*3
    high=[-math.inf]*3
    volume=0.
    for row in struct.iter_unpack('<12fH',data[84:]):
        a,b,c=row[3:6],row[6:9],row[9:12]
        require(all(math.isfinite(x) for x in row[:12]),'Non-finite triangle')
        for p in (a,b,c):
            for i in range(3):
                low[i]=min(low[i],p[i]); high[i]=max(high[i],p[i])
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    error=max(abs(a-b) for a,b in zip(low+high,reference['bounds_mm']))
    relative=abs(abs(volume)-reference['volume_mm3'])/reference['volume_mm3']
    require(error<.02,f'Mesh scale/envelope mismatch: {error} mm')
    require(relative<.002,f'Mesh volume mismatch: {relative}')
    return {'triangles':count,'bounds_mm':low+high,'envelope_error_mm':error,
            'relative_volume_error':relative}


def main():
    target=ROOT/'output'/'houdini'
    target.mkdir(parents=True,exist_ok=True)
    references=json.loads((OUT/'parts_validation.json').read_text())
    for name in references:
        require(not (target/(name+'.stl')).exists(),'Refusing to overwrite '+name)
    sw=connect()
    settings=[('Integer',78,3),('Integer',211,0),('Double',2,.000005),
              ('Double',3,math.radians(5)),('Toggle',69,True),('Toggle',70,False),
              ('Toggle',71,True),('Toggle',191,False)]
    previous=[]
    report={'units':'mm','coordinates':'native part coordinates','parts':{}}
    try:
        for kind,key,value in settings:
            suffix=kind if kind=='Toggle' else kind+'Value'
            getter=getattr(sw,'GetUserPreference'+suffix)
            setter=getattr(sw,'SetUserPreference'+suffix)
            previous.append((setter,key,getter(key)))
            setter(key,value)
            actual=getter(key)
            require(abs(actual-value)<1e-10,f'STL preference {kind} {key}: requested {value}, got {actual}')
        for name,reference in references.items():
            doc=reopen(sw,OUT/(name+'.SLDPRT'))
            active,error=sw.ActivateDoc3(doc.GetTitle(),False,0,0)
            require(active and error==0,'Cannot activate part')
            path=target/(name+'.stl')
            save_new(sw,doc,path)
            # SOLIDWORKS may capitalize STL; keep our exported names consistent.
            for actual in target.iterdir():
                if actual.name.lower()==path.name and actual.name!=path.name:
                    actual.rename(path)
            report['parts'][name]=check_stl(path,reference)
            (target/'mesh_validation.json').write_text(json.dumps(report,indent=2))
            sw.CloseDoc(doc.GetTitle())
            print('VALIDATED MESH',name,report['parts'][name]['triangles'],flush=True)
    finally:
        for setter,key,value in reversed(previous):
            setter(key,value)
        close_session(sw)


if __name__=='__main__':
    main()
