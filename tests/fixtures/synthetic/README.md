# Synthetic input fixtures v1

Dataset in `v1/`: seed `20261019`, zero additional deliveries.
Eight base delivery scenarios, including independent A/B/C examples from
contracts 06/07, plus explicit anomalies, replays and invalid inputs.

`manifest.json` contains configuration, record counts, file hashes and
**expected business results, not observed ingestion or checking results**.
`SHA256SUMS` includes all files except itself, including the manifest.

Document artifacts are `.synthetic.json` references. They are not PDF/XML,
parser output or accepted documents. Their declared fields are educational
fixture data for future F4 work. Envelope `media_type` specifies the intended
future document format; no actual PDF checksum is claimed in the envelope.
`document_references.jsonl` hashes the synthetic JSON bytes themselves.

`arrival_plan.jsonl` stores external reception order separately from business
payloads. It is a planned sequence, not proof of acceptance or a database run.
`valid/` contains coherent contract inputs, including deliberate business
divergences. `replays/` repeats identical content. `anomalies/` preserves
changed identity alternatives. `invalid/` contains structural negatives only.

Order/delivery reference files use a documented educational adapter derived
from model 07; no external order API contract is asserted.

Generated larger datasets belong under ignored `data/generated/`, never here.
Regeneration must use a new destination; the generator never overwrites.
Small fixture bytes are fixed to UTF-8/LF by `.gitattributes`.
