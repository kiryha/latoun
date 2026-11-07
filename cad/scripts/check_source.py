"""Compare native body envelopes and sampled surfaces with current input meshes."""
import json
import math
from sw_helpers import *
from model_layout import ASSETS

ALIASES={'plate_face_1gang':'1gang_plate_metal','plate_back_1gang':'1gang_plate_silicone',
         'insert_switch':'switch_insert','switch_collar':'switch_bezel',
         'insert_dimmer':'dimmer_insert','dimmer_neck':'dimmer_collar'}


def main():
    design=json.loads((INPUT/'design.json').read_text())
    components={c['id']:c for c in design['components']}
    report={'input':str(INPUT),'method':'Exact native bounds and up to 48 source vertices per body; not a full surface-distance proof','assets':{}}
    sw=connect()
    try:
        for asset in design['assets']:
            name=asset['file_stem']
            if name not in ASSETS: continue
            doc=reopen(sw,OUT/(name+'.SLDPRT'))
            bodies={interface(b,'IBody2').Name:interface(b,'IBody2') for b in interface(doc,'IPartDoc').GetBodies2(0,False)}
            rows=[]
            for instance in asset['instances']:
                source=components[instance['component_id']]
                matrix=instance['local_to_product']
                body_name=ALIASES.get(source['id'],source['id'])
                if source['id']=='screw_head': body_name='upper_fixing_head' if matrix[1][3]>0 else 'lower_fixing_head'
                body=bodies[body_name]
                bounds=[]
                for direction in [(-1.,0.,0.),(0.,-1.,0.),(0.,0.,-1.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]:
                    ok,x,y,z=body.GetExtremePoint(*direction,0.,0.,0.)
                    require(ok,'Cannot evaluate source comparison bounds')
                    bounds.append((x,y,z)[next(i for i,v in enumerate(direction) if v)]*1000)
                vertices=[]
                for line in (INPUT/source['reference_mesh']).read_text().splitlines():
                    if line.startswith('v '):
                        p=[float(v) for v in line.split()[1:4]]+[1.]
                        vertices.append([sum(matrix[i][j]*p[j] for j in range(4)) for i in range(3)])
                measured=[min(p[i] for p in vertices) for i in range(3)]+[max(p[i] for p in vertices) for i in range(3)]
                faces=[interface(f,'IFace2') for f in body.GetFaces()]
                distances=[]
                for p in vertices[::max(1,math.ceil(len(vertices)/48))]:
                    q=[v/1000 for v in p]
                    distances.append(min(math.dist(q,f.GetClosestPointOn(*q)[:3])*1000 for f in faces))
                rows.append({'body':body_name,'native_bounds_mm':bounds,'source_mesh_bounds_mm':measured,
                    'max_bound_difference_mm':max(abs(a-b) for a,b in zip(bounds,measured)),
                    'sample_count':len(distances),'max_sample_surface_distance_mm':max(distances)})
                print('COMPARED',body_name,rows[-1]['max_bound_difference_mm'],max(distances),flush=True)
            report['assets'][name]=rows
            write_report('source_comparison.json',report)
            close_session(sw,exit_app=False)
    finally:
        close_session(sw)


if __name__=='__main__': main()
