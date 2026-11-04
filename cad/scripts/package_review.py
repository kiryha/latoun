"""Package only validated 004 deliverables; never replace a prior package."""
import json
import math
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
native=ROOT/'output'/'solidworks'/'004'
step=ROOT/'output'/'step'/'004'
exports=json.loads((step/'step_validation.json').read_text())
assert len(exports)==14 and all(r['reopened'] for r in exports.values())
assert len([p for p in native.glob('*.SLDPRT') if not p.name.startswith('~$')])==12
assert len([p for p in native.glob('*.SLDASM') if not p.name.startswith('~$')])==2
for variant,count in [('Toggle',8),('Dimmer',9)]:
    report=json.loads((native/f'Latoun_{variant}_004_validation.json').read_text())['reopened']
    assert len(report['components'])==count and len(report['mates'])==count-1
    for c in report['components']:
        stem=Path(c['path']).stem
        angle=math.radians(25 if stem.startswith(('Switch_Stem','Switch_Grip')) else 0)
        expected=[1,0,0,0,math.cos(angle),math.sin(angle),0,-math.sin(angle),math.cos(angle),0,0,-.01 if angle else 0,1,0,0,0]
        if stem=='Fixing_Head_004':
            assert abs(abs(c['transform'][10])-.0415)<1e-9
            expected[10]=c['transform'][10]
        assert max(abs(a-b) for a,b in zip(c['transform'],expected))<1e-9

readme='''# Latoun revision 004 — design review / quotation

Open solidworks/Latoun_Toggle_004.SLDASM or Latoun_Dimmer_004.SLDASM
in SOLIDWORKS 2026. Keep all 12 SLDPRT files beside the two assemblies.
Parts contain native editable features. Assemblies use static lock mates.

For SOLIDWORKS 2016, use the AP214 files in step/. Each assembly STEP
contains its component solids. Individual part STEP files are also included.
STEP preserves geometry rather than the native feature history or mates.
Exports were reopened and checked in SOLIDWORKS 2026; 2016 was unavailable.

Plate: 70 x 120 x 3 mm. Revised 004 references govern other dimensions.
The draft intentionally retains stem/grip and dimmer stack overlaps.
Shaft openings, retention, mechanisms, threads, materials and production
tolerances remain unspecified. This is an appearance and quotation model.
See docs/model_structure_004.md and docs/assumptions_004.md for details.

Validation: 12 valid single-solid parts, 8/9 component assembly instances,
7/8 healthy mates, preserved positions, saved/reopened native documents,
and 14 AP214 exports reopened with valid solid counts and checked volumes.
'''
package=ROOT/'output'/'Latoun_004_review_package.zip'
assert not package.exists(),f'Refusing to overwrite {package}'
with zipfile.ZipFile(package,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('README.md',readme)
    for folder,label,patterns in [(native,'solidworks',['*.SLDPRT','*.SLDASM','*.json','*.bmp']),
                                  (step,'step',['*.step','*.json'])]:
        for pattern in patterns:
            for p in sorted(folder.glob(pattern)):
                if p.name.startswith('~$'):
                    continue
                z.write(p,f'{label}/{p.name}')
    for name in ['model_structure_004.md','assumptions_004.md','reference_inventory_004.md']:
        z.write(ROOT/'docs'/name,'docs/'+name)
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    print('PACKAGE VERIFIED',package,len(z.infolist()),'files',package.stat().st_size,'bytes')
