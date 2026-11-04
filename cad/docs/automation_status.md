# SOLIDWORKS automation prerequisite check

Date: 2026-11-04. **Partially verified; unattended save/reopen smoke test has not passed.** No product parts, assemblies or STEP exports have been generated.

## Confirmed

- SOLIDWORKS executable: `D:/programs/SOLIDWORKS/SOLIDWORKS/SLDWORKS.exe`, file version `34.4.1.1011`.
- COM ProgID `SldWorks.Application` is registered and resolves to that executable.
- A Python COM session reported revision `34.4.1` and initially zero open documents.
- The visible application identifies itself as **SOLIDWORKS Design Premium 2026 SP4.1**, rather than the Professional edition stated in the task. No extra edition-specific capability is assumed.
- Python 3.10.8 x64 is available. The system interpreter initially lacked pywin32. A project `.venv` now contains pywin32 312; no global Python packages were changed.
- Default part template exists at `C:/ProgramData/SolidWorks/SOLIDWORKS 2026/templates/Part.prtdot`.
- Local 2026 `sldworks.tlb`, `swconst.tlb`, .NET interop assemblies and API help are installed.
- API calls created an isolated test cylinder: centered 20 mm diameter sketch with a driving dimension and native `Test_Extrude` boss of 5 mm. The UI showed a fully defined sketch and one solid body. This is a verification object, not Latoun product geometry.

## Restrictions and findings

1. In the sandbox, attaching to the active COM object failed (`MK_E_UNAVAILABLE`) and creating it failed with access denied. Explicitly approved execution outside the sandbox allowed COM access. No corporate security settings were changed.
2. Normal automatic COM type-information lookup returned `TYPE_E_ELEMENTNOTFOUND` / invalid-index errors. Generating Python bindings from the installed type libraries and explicitly querying the required interfaces allowed modeling calls to work. This is a binding workaround, not a registry repair.
3. The application's dimension-entry preference opened a modal during the first sketch test. One UI recovery accepted the existing 20 mm test dimension. The script now temporarily disables `swInputDimValOnCreate` through the API and restores it in normal completion/error handling.
4. Validation stalled after native extrusion creation. The script version then used `IBody2.Check3`; the exact blocked call in that original client was not captured. A second diagnostic client stalled in COM attachment. Those clients were stopped without terminating SOLIDWORKS.
5. The script now uses the documented older `IBody2.Check` validity result (1=valid, 0=invalid), with progress logging and periodic Python tracebacks. An earlier test incorrectly expected zero from this older API and reported failure; that was a test-code error, not evidence of corrupt geometry.
6. Retrying attachment after stopping the clients still stalled in `pythoncom.connect`. The final diagnostic client was stopped too. SOLIDWORKS remains open with unsaved API-created test documents; no native output files exist under `output`.
7. Forced client termination prevented the normal `finally` cleanup. **The test session's input-dimension-value prompt may remain disabled.** A UI attempt to open options produced no observable response. After restarting, check System Options > General > Input dimension value and restore it to enabled. Do not assume the normal preference restoration ran in the interrupted test.

## What remains unverified

- Complete automated body/feature/dimension checks.
- Successful native test-part save and reopen, and persistence of its editable feature tree.
- Reliable unattended completion and cleanup of a fresh session.
- Product modeling, mates, interference, STEP export and factory-side import.

The isolated runs are recorded under `output/verification`. Failure logs do not indicate successful output: a `test_part` path in a log is the intended destination, not proof that the file exists.

## Smallest practical next step

Close/relaunch only the API-created test session after preserving any user work and restore the dimension-input preference noted above, then run `scripts/verify_solidworks.py` once outside the sandbox using the already approved execution path. The revised script suppresses the dimension prompt, uses explicit local interfaces and logs the validation stage. If fresh-session COM still stalls, reproduce the same small test with the installed .NET interop in a C# STA process, or have the SOLIDWORKS administrator inspect type-library registration. Do not modify registration or disable security controls automatically.

The test script's `--show-session` option only exposes the session. `--inspect-session` is a diagnostic option for the active test cylinder; it must not be run against an unrelated user design. Test geometry is intentionally isolated from `output/solidworks`.

## API references

Method signatures were inspected directly from the installed 2026 interop assemblies. Official web help was also consulted, including [native extrusion](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ifeaturemanager~featureextrusion3.html), [body-validity examples and return semantics](https://help.solidworks.com/2024/english/api/sldworksapi/Check_Bodies_for_Faults_Example_VB.htm), and [body mass-property ordering and units](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ibody2~getmassproperties.html). Where 2026 web pages were unavailable, installed 2026 signatures were the authority.
