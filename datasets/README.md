# Datasets: Catalog + What They Contribute

This project relies on **public datasets** that cover complementary layers:

1) **Activation** (spikes, calcium, fMRI): “what changed?”
2) **Biochemistry / receptors** (PET, gene expression): “what could be modulated?”
3) **Wiring** (projections, single-neuron reconstructions): “how effects propagate?”

Below are the recommended “first-class” sources for a general-purpose tool.

---

## Mouse (activation)

### IBL Brain-Wide Map (Neuropixels during decision task)
- Landing: https://www.internationalbrainlab.com/brainwide-map
- AWS Open Data: https://registry.opendata.aws/ibl-brain-wide-map/
- Data access tooling: ONE (Open Neurophysiology Environment)
  - Docs: https://int-brain-lab.github.io/ONE/
  - Quickstart: https://docs.internationalbrainlab.org/notebooks_external/one_quickstart.html

What we extract:
- Region-level activity summaries per task variable (e.g., choice, reward)
- Session metadata (subject, lab, insertion coordinates)
- Optional: spike trains for deeper models

---

### Allen Brain Observatory (Neuropixels + 2P calcium)
- AWS Open Data: https://registry.opendata.aws/allen-brain-observatory/
- AllenSDK access example: https://allensdk.readthedocs.io/en/latest/_static/examples/nb/ecephys_data_access.html
- Neuropixels tutorial: https://alleninstitute.org/science-resource/allen-brain-observatory-neuropixels-dataset-tutorial/

What we extract:
- Stimulus-aligned tuning curves / response amplitudes
- Cross-area comparisons in standardized conditions

---

### MICrONS (dense functional + EM connectomics; cortical volume)
- Portal: https://www.microns-explorer.org/

What we extract:
- Local microcircuit constraints (synapse-level graph, functional responses)
- Useful for “does the local microcircuit agree with our region-level propagation?”

---

## Mouse (biochemistry / receptors / cell types)

### Allen Mouse Brain Atlas (ISH gene expression)
- API docs: https://brain-map.org/support/documentation/api-for-mouse-brain-atlas
- API endpoint entry: https://mouse.brain-map.org/static/api

What we extract:
- Gene expression summaries for receptor/transporters (e.g., Slc6a4, Htr*, Adora2a)
- Region-level and optionally voxel-level grids (when available)

---

### Allen Brain Cell Atlas (ABC Atlas) + MERFISH whole mouse brain
- ABC Atlas landing: https://brain-map.org/bkp/explore/abc-atlas
- Data access docs: https://alleninstitute.github.io/abc_atlas_access/intro.html
- MERFISH dataset entry example: https://knowledge.brain-map.org/data/5C0201JSVE04WY6DMVC

What we extract:
- Cell-type enriched receptor expression (where genes are available in panels)
- Spatial cell-type composition for each region

---

### Allen Mouse CCF (Common Coordinate Framework)
- CCF 2020 distribution details: https://alleninstitute.github.io/abc_atlas_access/descriptions/Allen-CCF-2020.html

What we extract:
- Region hierarchy and IDs (canonical indexing)
- Reference volumes for registration and resampling

---

## Mouse (wiring)

### Allen Mouse Brain Connectivity Atlas (mesoscale projections)
- AllenSDK docs: https://allensdk.readthedocs.io/en/latest/connectivity.html

What we extract:
- Region-to-region projection strength matrices
- Optional: cell-type specific projections where available

---

### MouseLight (single-neuron whole-brain reconstructions)
- Project home: https://www.janelia.org/project-team/mouselight
- Resources: https://www.janelia.org/project-team/mouselight/resources

What we extract:
- Long-range projection motifs (single-neuron paths) to validate propagation assumptions

---

## Human (biochemistry / receptors)

### PET receptor atlas (19 receptors/transporters)
- Paper: https://www.nature.com/articles/s41593-022-01186-3
- Data + code: https://github.com/netneurolab/hansen_receptors

What we extract:
- Cortical receptor density maps (parcellated and/or surface/volume, depending on resource)
- Baseline priors for receptor availability

---

### JuSpace (PET/SPECT neurotransmitter maps toolbox + sources)
- Code: https://github.com/juryxy/JuSpace
- Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC7814756/

What we extract:
- Additional PET/SPECT maps not in hansen_receptors
- Reference workflows for PET–MRI spatial correlation

---

## Human (transcriptomics)

### Allen Human Brain Atlas (AHBA) microarray
- Data download: https://human.brain-map.org/static/download
- Docs: https://brain-map.org/support/documentation/human-brain-atlas-microarray-data-download
- API: https://brain-map.org/support/documentation/human-brain-atlas-api

Recommended processing:
- `abagen` docs: https://abagen.readthedocs.io/

What we extract:
- Region-level gene expression (with careful donor normalization)

**Local fixtures:**
- `human_ahba_expression_fixture.csv`: Sample parcellated expression data for testing (4 genes × 6 regions)
  - Used for offline unit tests
  - Real AHBA data can be loaded via `abagen` (optional dependency)

---

## Human (activation)

### OpenNeuro (BIDS imaging repository)
- Portal: https://openneuro.org/

What we extract:
- A generic BIDS ingestion path (task fMRI, resting fMRI, PET, etc.)
- For pharmaco-fMRI, users will typically add their own datasets; we provide adapters.

---

## Data licensing and provenance
**Stop here and read `governance/README.md` before mixing sources.**
Some sources have noncommercial terms or attribution requirements.
