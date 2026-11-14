# Open-source research from ASTRA → AETHERION

**Read from previous design:** `huyng0699-arch/NASA-Space-Apps/docs/ux/ASTRA_UX_REACCEPTANCE_OPEN_SOURCE_20261114.md`, not from an invented new list. The references below are for studying **the new AETHERION native Qt architecture**.

| Upstream | Specific adaptation target | License assessment | Gate |
|---|---|---|---|
| PyVistaQt | QtInteractor embedded 3D and mesh object/picking behavior for Body Atlas | MIT; keep original license and copyright | Original snapshot imported; real PySide6/Windows spike NOT YET TESTED |
| VisPy | GPU scene canvas, 3D meshes and camera controls | BSD-3-Clause; preserve notices | Compare against PyVistaQt on Windows |
| PyQtGraph | Time-aware charts, point selection and provenance detail | MIT; preserve copyright | Validate with real API observations |
| NASA Open MCT | Timeline, source badges, telemetry browse and event UX | Apache-2.0; preserve NOTICE/license | **Design reference only**: Web app cannot substitute native Qt app |
| napari | Source-linked layer selection, anatomy overlays, keyboard UX | BSD-3-Clause | Research only until measured Qt integration |
| 3D Slicer | Anatomy viewer and data model concept | BSD-style with additional terms; check exact obligations | Research only; do not bundle whole app into runtime |

Source snapshots are kept under `Các mã nguồn mở tham khảo/`, *not* under the live `apps/server` or `apps/desktop`. No user-facing 3D claim is accepted until a real depth-buffered native renderer, camera controls, object picking, Windows evidence and independent medical asset licensing are verified.

## Risk register
- Source code licenses do **not** automatically license 3D patient anatomy models, NASA graphics, scientific PDFs or other embedded external data.
- Some upstream dependencies are large and can increase a distributed EXE's size; measure before selecting.
- Do not use GitHub Actions import success as proof that the app itself works.
- Source SHA and per-file Git hashes are preserved in the lock and generated manifests.
