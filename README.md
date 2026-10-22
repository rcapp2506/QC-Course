# QC-Course

Course notebooks for quantum computing, organised by hardware ecosystem, plus a
written lesson on RSA and Shor's algorithm.

## Layout

```
IBM/      the original course notebooks on the IBM Qiskit stack
          (qiskit, qiskit-aer, qiskit-ibm-runtime), with fixes applied.
IQM/      the same notebooks re-backended for IQM Garnet (20q) & Emerald (54q)
          on IQM Resonance; shared helper iqm_backend.py + README.
lesson/   rsa_shor_lesson.tex — a detailed lesson on RSA and Shor's algorithm,
          companion to IBM/shor.ipynb and IQM/shor.ipynb.
```

## Quick start

**IBM / simulator (no account needed):**
```bash
pip install qiskit qiskit-aer matplotlib pandas
jupyter notebook IBM/shor.ipynb
```

**IQM Garnet/Emerald (IQM Resonance):**
```bash
pip install "qiskit-iqm>=18" matplotlib pandas
export IQM_TOKEN="<token from https://resonance.iqm.tech/>"
jupyter notebook IQM/shor.ipynb      # edit the single TARGET line to pick the backend
```
See `IQM/README.md` for the full backend-selection table (local fake sim → cloud mock → real QPU).

## Highlights

- **`IBM/shor.ipynb` / `IQM/shor.ipynb`** — an enriched, end-to-end Shor's algorithm:
  period finding → order→factor reduction → QPE circuit → continued fractions →
  a robust `shor_factor(N)` → **breaking a toy RSA key**. Verified to run on Qiskit/Aer.
- **`lesson/rsa_shor_lesson.tex`** — the theory behind it, with all theorems stated and
  explained, worked examples, and a step-by-step Shor recipe.

## What changed per folder

- `IBM/`: updated the retired `channel="ibm_quantum"` → `ibm_quantum_platform`
  (sunset in 2025); enriched the Shor notebook. See `IBM/README.md`.
- `IQM/`: Qiskit circuit notebooks re-backended to the IQM native gate set (PRX + CZ)
  via `transpile_to_IQM` + `IQMProvider`/`backend.run`; ML notebooks carry an IQM note.
  See `IQM/README.md`.
