# Regression tests

Golden-file characterization tests for the CardioMechanics binaries. Each test
runs a binary on a fixed input and compares its output to a committed reference
with numerical tolerances (never byte-exact). See `REGRESSION_PLAN.md` for the
full design and rollout.

Coverage so far:
- **CellModelTest** — all runnable single-cell ionic models (auto-discovered),
  plus coupled ionic+tension runs for Land17. Serial.
- **CardioMechanics** — benchmark2015 Problem1 (Static solver) at `mpirun -np 4`:
  the `Pressure.dat` time series and the final deformed geometry (last VTU point
  coordinates, via meshio). Marked `mpi`.

Planned: EM01 full electromechanical run, BidomainMatrixGenerator, acCELLerate.

## Setup

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r tests/requirements.txt
```

## Run

```sh
pytest tests/                 # all
pytest tests/ -k cellmodel    # one binary
pytest -m "not slow"          # skip long integration cases
pytest -m "not mpi"           # skip parallel cases
```

## Regenerate goldens

After an *intended* behaviour change, rebaseline and review the diff before
committing:

```sh
pytest tests/ --update-golden
git diff tests/**/golden
```

## Notes

- **Binary discovery:** set `$CM_BIN_DIR` to pin a build directory, otherwise the
  newest match of `_build/*/bin/**/<name>` is used (release/debug/installed
  agnostic).
- **kaRootDir:** the run fixture sets `kaRootDir` to the repo root in the
  subprocess environment. Without it the binaries segfault at startup.
- **Goldens** were generated on this machine (PETSc 3.24, serial). Cross-environment
  drift is absorbed by tolerances, not per-platform goldens.

## Known non-functional models

The following cell models do not run standalone in the current repo and are
excluded from the CellModelTest suite (`KNOWN_BROKEN` in
`cellmodel/test_cellmodel.py`). These are pre-existing legacy defects, not
regressions — to be investigated separately:

- `HimenoEtAl_Endo`, `HimenoEtAl_Epi`, `HimenoEtAl_Mid` — each tries to open a
  base `HimenoEtAl.ev` that is not shipped in `electrophysiology/data/`.
- `Kurata` — fails parameter initialization ("Init elphy parameters failed").
