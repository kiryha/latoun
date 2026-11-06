"""CAD product hierarchy. Asset groups mirror the read-only application manifest."""
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
# Entries: native model basename, X rotation (degrees), Y and Z translation (mm).
ASSEMBLIES={
    '1gang_switch': [('1gang_plate',0,0,0),('1gang_plate_screws',0,0,0),('1gang_slot1_switch',0,0,0)],
    '1gang_dimmer': [('1gang_plate',0,0,0),('1gang_plate_screws',0,0,0),('1gang_slot1_dimmer',0,0,0)],
}
ASSETS={
    '1gang_plate':'plate.1gang',
    '1gang_plate_screws':'hardware.1gang.plate_screws',
    '1gang_slot1_switch':'module.1gang.slot1.switch',
    '1gang_slot1_dimmer':'module.1gang.slot1.dimmer',
}
PRODUCTS=('1gang_switch','1gang_dimmer')


def check_manifest():
    manifest=json.loads((ROOT.parent/'config/wall_plates/asset_manifest.json').read_text(encoding='utf-8'))
    for name,asset_id in ASSETS.items():
        entry=manifest['parts'][asset_id]
        if Path(entry['file']).stem!=name or not entry['is_active']:
            raise RuntimeError('CAD asset does not match active manifest entry: '+asset_id)


def native_filename(name):
    return name+('.SLDASM' if name in ASSEMBLIES else '.SLDPRT')


def pose_values(angle=0,y=0,z=0):
    a=math.radians(angle)
    c,s=math.cos(a),math.sin(a)
    return [1.,0.,0.,0.,c,s,0.,-s,c,0.,y/1000,z/1000,1.,0.,0.,0.]


def instances(name):
    counts=Counter()
    for child,a,y,z in ASSEMBLIES[name]:
        counts[child]+=1
        yield child+'-'+str(counts[child]),child,a,y,z


def leaf_instances(name,prefix='',parent=(0,0,0)):
    pa,py,pz=parent
    c,s=math.cos(math.radians(pa)),math.sin(math.radians(pa))
    for instance,child,a,y,z in instances(name):
        pose=(pa+a,py+c*y-s*z,pz+s*y+c*z)
        full=prefix+instance
        if child in ASSEMBLIES:
            yield from leaf_instances(child,full+'/',pose)
        else:
            yield full,child,pose_values(*pose)
