# Third-party licenses and provenance

AETHERION's top-level Apache-2.0 license covers only project-owned original contributions. It does **not** relicense libraries, NASA resources, images, research texts or device firmware.

| Component | Purpose | License / license reference | Original source | Status |
| --- | --- | --- | --- | --- |
| Python | Runtime | Python Software Foundation License | https://www.python.org/psf/license/ | Required locally |
| FastAPI | HTTP service | MIT | https://github.com/fastapi/fastapi | Declared dependency |
| Uvicorn | ASGI server | BSD-3-Clause | https://github.com/encode/uvicorn | Declared dependency |
| Pydantic | Request validation via FastAPI | MIT | https://github.com/pydantic/pydantic | Transitive dependency |
| PySide6 / Qt for Python | Native Qt desktop | LGPLv3 / GPLv3 / commercial terms (verify exact distribution and Qt modules) | https://doc.qt.io/qtforpython-6/licenses.html | Declared dependency; packaging review required |
| NASA Space Apps official challenge | Challenge citation, not bundled software | Refer to NASA's stated terms | https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/ | Linked only |

## Before any release

1. Confirm exact library versions, transitive dependencies, redistribution terms and notices for the binary distribution.
2. Inspect each imported NASA dataset, photograph, diagram, scientific publication and 3D model for source, reuse rights, author, modification history and attribution.
3. Do not present NASA branding as an endorsement.
4. List all substantial external sources in the official challenge's project submission references.
5. Do not use third-party text or figures without the necessary permission or license.

This is an initial compliance inventory, **not a complete license audit**.

## Vendored development references (not AETHERION runtime dependencies)

The full **PyVistaQt** upstream source snapshot is preserved at `Các mã nguồn mở tham khảo/pyvistaqt/` with the original `LICENSE` and copyright notices. Source revision: `ad706903962a533032218e92f39e1a315eaf949f`; 51/51 tracked Git blobs verified. **MIT**: The PyVista Developers (2017–2026).

The following additional references were named in ASTRA's 14 November 2026 reuse guidance, pinned but **not yet copied or independently redistributed**: VisPy (BSD-3-Clause), PyQtGraph (MIT), NASA Open MCT (Apache-2.0), napari (BSD-3-Clause), and 3D Slicer (BSD-style license with additional provisions). Exact repositories and commits: `Các mã nguồn mở tham khảo/SOURCES.lock.json`.

Bundling a source snapshot is not an authorization to incorporate external anatomical meshes, NASA graphics, medical data, or third-party bundled assets into a commercial product. Their rights need separate review.
