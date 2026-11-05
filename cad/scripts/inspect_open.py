from sw_helpers import *
sw=connect()
allowed={p.name.lower() for p in OUT.glob('*.SLDPRT')}|{'1gang_switch.step.sldprt'}
for obj in sw.GetDocuments() or []:
    d=interface(obj,'IModelDoc2')
    require(not d.GetPathName() and d.GetTitle().lower() in allowed,'Unexpected document; preserving session')
require(sw.CloseAllDocuments(True),'Cannot close our temporary imports')
require(not sw.GetDocuments(),'Temporary documents remain')
sw.ExitApp()
print('Temporary STEP documents closed; SOLIDWORKS exited',flush=True)
