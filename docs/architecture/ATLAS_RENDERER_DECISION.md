# AETHERION 3D renderer decision — provisional technical baseline

**Quest:** Q-0122. **Status:** PREPARE / implemented backend policy; Windows benchmark and independent acceptance **PENDING**.  
**Date:** 2026-11-14. **Product:** native PySide6 Desktop, bilingual VI/EN.

## One actual renderer, one honest fallback

**Current code-backed 3D renderer:** PyVistaQt `QtInteractor` + PyVista + VTK,
under `apps/desktop/src/aetherion_desktop/render3d/backend_policy.py`.
The live `BodyAtlas3D._render` in `atlas3d.py` now obtains the renderer from
`load_native_renderer()` instead of importing a second/rendering backend
inline. An incompatible Qt binding raises `RuntimeError`: the real Qt page
shows the explicitly labelled **2D source-backed anatomy list** from Q-0131.
2D is not presented as mesh picking or 3D.

The canonical backend choice is **provisional**, not a completed Q-0121
PyVistaQt-vs-VisPy Windows benchmark or an approved EXE payload.

| Evaluation dimension | PyVistaQt / VTK in AETHERION | VisPy candidate | Evidence gap |
| --- | --- | --- | --- |
| Actual Desktop code | Integrated `QtInteractor`; loads SHA-verified mesh; calls `enable_mesh_picking` | No integrated Desktop path | Native Windows test of camera, pan, zoom and actual picking |
| Qt integration | Same PySide6 window through QtPy; guard rejects wrong Qt binding | Alternative GL canvas; would need additional native integration | Windows 10/11 high-DPI / GPU driver compatibility |
| Mesh rendering | Existing VTK code and approved STL/OBJ/PLY metadata | Needs separate asset/picking implementation | Compare same exact SHA-256-checked 3D models, not stand-in 2D |
| Native libraries / EXE size | VTK + PyVistaQt/PyVista/PySide6; must measure installed `.dll` / `.pyd` bytes and final frozen EXE | Not imported; must measure an isolated VisPy build | **No measured Windows DLL size or packaged file size** |
| Performance | Unknown FPS and mesh pick latency on Windows | Unknown FPS and mesh pick latency on Windows | **No A/B benchmark**, no fabricated numbers |
| License | Package metadata dynamically inspected; actual upstream + model rights still require file-level review | Not audited locally; imported source is not a license approval | Approval of complete license manifests, attributions and redistribution |
| No GPU/native 3D | Genuine keyboard-operable **2D** fallback with approved source metadata | No second fake renderer | Real Windows fallback verification |

## Reproducible installed-environment audit (no guessing)

Use the same Python environment intended for a Windows Desktop package:

```powershell
$env:PYTHONPATH = "apps/desktop/src"
python -c "from aetherion_desktop.render3d.backend_policy import inspect_installed_renderer as f; print(f())"
```

This reports each **installed** PySide6, PyVista, PyVistaQt and VTK
distribution's version, license string **as reported by package metadata**
(not independent legal verification), number of native extension/library
files and their actual local byte count. Missing packages report `None`,
not an invented zero-impact dependency. `dll_audit_complete=False`,
`measured_fps=None` and `measured_picking_ms=None` deliberately remain
unverified. On Windows, the audit needs additional review of transitive DLLs,
plugins and the final PyInstaller output; package metadata alone cannot
certify compliance or successful freezing.

For the **future Q-0121 Windows comparison**, measure each candidate in
separate clean environments with the same licensed model SHA, Windows
build/GPU, resolution (1040×650 and 1600×900), DPI 100%/150%, first-frame
latency, orbit FPS, reset camera, ray/triangle picking latency, peak RAM,
GPU memory and cold EXE size. Capture actual versions, commands and
screenshots/logs; do not claim one renderer is faster without measurements.

## Constraints and acceptance

- No new Qt application, HTTP server or observation store is introduced.
- No changes to NASA source files, educational anatomy STL bytes, license
  registry, subject identity or clinical decisions.
- A `READY` result from any metadata scan does **not** prove 3D render
  success. Verify a real selected mesh triangle under native Qt on Windows.
- Q-0121 (Windows A/B renderer comparison) and Q-0002 (Windows native Qt)
  remain final dependencies. Q-0468 genuine PyVistaQt Atlas and Q-0131 true
  2D fallback remain independently reviewable components.
- **Final decision:** pending measured Windows A/B and independent reviewer.
  **Interim engineering default:** preserve the existing sole working code
  path PyVistaQt + honest 2D fallback; do not add a speculative VisPy backend.

