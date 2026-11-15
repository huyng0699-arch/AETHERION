# NASA IMPACT condition list and CliFF archive

The source for the 119-condition index is NASA's Exploration Medical Capability
Evidence Library Methods, HRP-48036 Revision B, Appendix C, November 2023.
The official list preserves its `ICL` identifiers, including ICL36A and
ICL36B, and omits conditions that NASA marks as removed.

- NASA publication: https://ntrs.nasa.gov/citations/20240004774
- Original PDF: https://ntrs.nasa.gov/api/citations/20240004774/downloads/HRP-48036%20RevB_ExMC%20Evidence%20Library%20Methods.pdf
- The server serves all 119 names with their PDF page anchors through
  `/api/v1/knowledge/conditions`.
- There are 118 extracted CliFF JSON documents. Their `CLIFF-` identifiers
  are local catalogue slots, not NASA ICL identifiers. The condition index
  links 116 related documents; the three remaining entries link to the
  primary NASA publication.
- NASA's ICL119 is venous thromboembolism, which is already present as
  `CLIFF-017`. Treating it as an additional `CLIFF-119` would duplicate
  that document. Local slot `CLIFF-119` is still unresolved.

The extracted text and its verification flags are archival claims, not
independent verification of original PDF bytes. The catalogue is read-only
research information, not validated clinical decision support.
