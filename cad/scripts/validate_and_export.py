"""Check saved solids, export AP214, and reopen the exports."""
import argparse
import json
import math
import faulthandler
import sw_helpers
from sw_helpers import *
from model_layout import ASSEMBLIES, ASSETS, check_manifest, native_filename


def validate_parts(sw):
    manifest=json.loads((VALIDATION/'parts_validation.json').read_text())
    from build_parts import check_asset
    report={}
    for name in ASSETS:
        record=manifest[name]
        doc=reopen(sw,OUT/native_filename(name))
        result=dict(record)
        result.update(check_asset(doc,name,[f['name'] for f in record['features']]))
        result.update(path=str(OUT/native_filename(name)),reopened=True,asset_id=ASSETS[name])
        report[name]=result
        close_session(sw,exit_app=False)
        print('CHECKED',name,flush=True)
    write_report('parts_validation.json',report)
    return report


def exports(sw,only=None):
    require(not sw_helpers.initial_documents,'Export requires a session without pre-existing documents')
    check_manifest()
    target=ROOT/'output'/'step'
    target.mkdir(parents=True,exist_ok=True)
    names=list(ASSETS)+list(ASSEMBLIES)
    if only:
        require(set(only)<=set(names),'Unknown export name')
        names=[n for n in names if n in only]
    report_path=VALIDATION/'step_validation.json'
    results=json.loads(report_path.read_text()) if report_path.exists() else {}
    old_ap=sw.GetUserPreferenceIntegerValue(75)
    try:
        require(sw.SetUserPreferenceIntegerValue(75,214),'Cannot set STEP AP214')
        for name in names:
            native=OUT/native_filename(name)
            step=target/(name+'.step')
            doc=reopen(sw,native,2 if name in ASSEMBLIES else 1)
            if name in ASSEMBLIES:
                from build_assembly import inspect_assembly
                expected=inspect_assembly(doc,name)['geometry']
            else:
                from build_parts import check_asset
                record=json.loads((VALIDATION/'parts_validation.json').read_text())[name]
                expected=check_asset(doc,name,[f['name'] for f in record['features']])
            if step.exists():
                saved={'preserved_existing':True}
            else:
                active,error=sw.ActivateDoc3(doc.GetTitle(),False,0,0)
                require(active and error==0,'Cannot activate export document')
                saved=save_new(sw,doc,step,2)
            require('AUTOMOTIVE_DESIGN' in step.read_text(errors='replace')[:5000],'STEP is not AP214')
            close_session(sw,exit_app=False)
            require(not sw.GetDocuments(),'Native documents remained open before STEP import')
            data=sw.GetImportFileData(str(step))
            try:
                imported,error=sw.LoadFile4(str(step),'',data,0)
                require(imported and error==0,f'STEP reopen failed: {error}')
                actual=solid_geometry(interface(imported,'IModelDoc2'))
                require(actual['solid_count']==expected['solid_count'],'STEP solid count mismatch')
                relative=abs(actual['volume_mm3']-expected['volume_mm3'])/expected['volume_mm3']
                require(relative<1e-4,'STEP volume mismatch')
                envelope_error=max(abs(a-b) for a,b in zip(actual['bounds_mm'],expected['bounds_mm']))
                require(envelope_error<.002,'STEP placement/envelope mismatch')
                for a,b in zip(actual['solid_volumes_mm3'],expected['solid_volumes_mm3']):
                    require(abs(a-b)/b<1e-4,'STEP component volume mismatch')
                results[name]={'path':str(step),'asset_id':ASSETS.get(name),'schema':'AP214','save':saved,
                    'reopened':True,'valid_solids':actual['solid_count'],'volume_mm3':actual['volume_mm3'],
                    'relative_volume_difference':relative,'envelope_error_mm':envelope_error}
                write_report('step_validation.json',results)
            finally:
                require(sw.CloseAllDocuments(True),'Cannot close temporary STEP documents')
            print('VALIDATED STEP',step.name,flush=True)
    finally:
        sw.SetUserPreferenceIntegerValue(75,old_ap)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--geometry-only',action='store_true')
    parser.add_argument('--export-only',action='store_true')
    parser.add_argument('--only',nargs='+',help='Export/check only these model basenames')
    args=parser.parse_args()
    check_manifest()
    sw=connect()
    faulthandler.dump_traceback_later(300,repeat=True)
    try:
        if not args.export_only:
            validate_parts(sw)
        if not args.geometry_only:
            exports(sw,args.only)
    finally:
        faulthandler.cancel_dump_traceback_later()
        close_session(sw)
