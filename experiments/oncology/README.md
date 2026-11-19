# Oncology experiments

This private project preserves the legacy catalogs, vector experiments and Boolean
simulator that previously lived under `babylon60`. It is maintained separately from
the BABYLON-60 execution kernel. The import namespace is `babylon60_oncology`;
there are no compatibility imports in the core package.

The base package uses Python's standard library. The optional Boolean simulator
and VSA benchmark use NumPy, NetworkX and pandas:

```sh
cd experiments/oncology
python -m pip install '.[simulation,dev]'
python -m pytest
babylon60-oncology-experiment --help
```

The project has its own package manifest and license. It is not a member of the
root installation or its optional extras. Building or installing BABYLON-60 does
not install this project. The existing `numpy` core dependency and unrelated
development/graph dependencies retain their own consumers.

## Data and generators

There are two distinct legacy catalog representations. They are preserved rather
than merged into an invented common model:

- `src/babylon60_oncology/data/oncology_300.json` is the exact versioned snapshot
  previously stored in `tests/fixtures/oncology_300.json`. The VSA engine reads
  this packaged resource by default, including after an isolated wheel install.
- `data/ontology-source.md` is a byte-preserved copy of
  `docs/02_ontology/axiom_oncologia_300_primitivas.md` at source commit
  `d4dc22030285ae7138cc3625a62e375618ef744a`. The original remains as historical
  documentation. `scripts/export_ontology.py` reads the local copy and emits
  JSON and Lean source.
- `data/primitives_catalog.json` is the separate list previously stored in
  `scripts/c5_isomorphisms/oncology_primitives_catalog.json`.
  `scripts/generate_primitives.py` reads it and emits Python, YAML and Markdown.
  The previously generated `oncology_primitives.py` is preserved in this package.

Both generators default to this project's ignored `generated/` directory. They
do not recreate modules under the core namespace:

```sh
python scripts/export_ontology.py
python scripts/generate_primitives.py
python scripts/generate_primitives.py --output-dir /tmp/oncology-generated
```

The first generator also accepts `--json-out` and `--lean-out`. These two
destinations must remain distinct after Unicode NFC normalization and case
folding. Canonically equivalent Unicode names and case-only variants are rejected
on every filesystem, including systems that otherwise distinguish them. This is
a deliberately conservative output restriction, checked before either file is
written; it does not assert that such names identify the same file on every
filesystem. Its Lean output
retains the explicit list-cardinality premise checked by the existing formal
regressions. Those compiler checks establish properties of the generated types
and lists; they do not validate a biological model.

## Scope

The data snapshots are versioned catalog material. Moving or packaging them is
not a review of their biological references. No validated biological edge set or
update rules have been added. The Boolean simulator retains its existing
self-loop fallback, correlations and numerical threshold. A successful run
reports the simulation's numerical result, without claiming suitability for an
in-vitro or clinical application.

`scripts/verify_catalog.py`, `scripts/cancer_isomorphism_pipeline.py` and the VSA
benchmark preserve historical demonstrations. In particular, the cancer script
prints a fixed payload with legacy `ATTESTED` wording and a hard-coded number;
this is not an observed attestation or measured result. The catalog verifier's
counts and substring checks do not establish a causal DAG or therapeutic
efficacy. Historical performance labels in the benchmark are not fresh hardware
measurements. These scripts are not invoked by the core CLI or release process.

The tests cover packaged resource access, deterministic vector operations,
existing toy trajectories, generator relocation and CLI help. They do not
certify clinical behavior or execution-kernel authorization.
