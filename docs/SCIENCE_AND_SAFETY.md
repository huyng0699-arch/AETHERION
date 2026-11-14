# Scientific integrity, data quality and safety

AETHERION is currently a hackathon/developer prototype. It is **not a medical device**, has no validated diagnostic performance and must not be used in real care settings or on space missions.

## Medical science boundaries

- **Xerostomia vs. salivary hypofunction, fatigue vs. pathology, sensor loss vs. patient event:** do not collapse subjective experience, objective measurement and missing data into one variable.
- Every observation requires a unit, measurement time, subject and origin. Self-reported values and sensor outputs must be distinguishable.
- An unmeasured quantity is *unknown*, not healthy, normal or zero.
- Clinical warning rules require provenance, expert review, testing, context, false-positive/false-negative analysis and a human escalation path.
- AI-generated text is not verified evidence. A deterministic safety layer, not an LLM, must control any future emergency escalation.
- In remote environments, recommendations must account for communications delay and absent professional support without inventing a treatment protocol.

## Privacy and security gates before public use

The initial API has no authentication and must run on **localhost only**, with non-sensitive engineering data. Any general-population deployment requires identity and role-based access, consent, safe retention/deletion, encryption, audit, security testing, interoperability safeguards and jurisdiction-specific regulatory assessments.

## Space qualification gates

No environmental, radiation, human-factors, reliability, hardware, software assurance, operational or clinical flight qualification has been conducted. The 2050 vision is an aspiration, not a NASA deployment or endorsement.

## Data provenance requirement

Every imported source must record title, issuing organization, URL/DOI, access date, publication/update date where available, licensing status, and whether the content is reproduced, adapted or only referenced. See `knowledge/nasa/SOURCES.md` and `submission/REFERENCES.md`.
