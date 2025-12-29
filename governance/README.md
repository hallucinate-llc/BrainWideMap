# Governance: Licensing, Provenance, Ethics, and Citation

This repo is a **data integration layer**, so licensing and provenance are non-negotiable.

---

## 1) Licensing basics

- Many neuroscience datasets are open but may require:
  - attribution (citation)
  - non-commercial restrictions
  - specific sharing rules

Action item:
- Maintain a `DATA_SOURCES.yml` file in the repo root that records:
  - dataset name
  - version/date accessed
  - license/terms
  - required citation
  - what we store locally vs link externally

---

## 2) Provenance requirements (technical)

Every derived artifact must store:
- source dataset id + version/date accessed
- transformation parameters
- software versions
- checksums of critical inputs

---

## 3) Human data

If you ingest human imaging data (BIDS), ensure:
- you have rights to use it
- you follow the dataset’s consent and usage constraints
- you do not leak identifying information

---

## 4) Ethics note on “therapeutics”

This repo produces mechanistic hypotheses, not medical advice.

Avoid:
- claims of clinical efficacy without appropriate evidence
- releasing tools that are easily repurposed for unsafe biological design
(Keep the toolkit focused on analysis/validation, not synthesis.)

---

## 5) Citation expectations

Add a `CITATIONS.md` once your core dataset list stabilizes.
Every paper/project that uses this toolkit should cite:
- the upstream datasets used
- any key transformation tools (e.g., AllenSDK, ONE, abagen, neuromaps)
