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
