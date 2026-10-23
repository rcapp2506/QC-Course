# QC-Course — IBM edition

The course notebooks on the **IBM Qiskit** stack (`qiskit` 2.x, `qiskit-aer`,
`qiskit-ibm-runtime`), numbered in the recommended study order (the table is in the root
`README.md`). The parallel `../IQM` folder contains the same notebooks re-backended for IQM
Garnet/Emerald on IQM Resonance, with the same numbering.

## Setup

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime matplotlib pandas pylatexenc
```

Everything except `09_Running_on_Hardware.ipynb` (and the optional hardware sections of 13 and 17)
runs on the local `AerSimulator`, so no account is needed. To run on real IBM hardware, see
`09_Running_on_Hardware.ipynb`: accounts authenticate with `channel="ibm_quantum_platform"` and a
token from https://quantum.cloud.ibm.com/ (the legacy `ibm_quantum` channel was retired in 2025).

`23_PENNY-QUANV.ipynb` needs `pennylane`, `tensorflow`/`keras` and the MNIST download.

## Provenance

The notebooks are the "v2.2 enhanced" set of the 2025-26 course (`../qc-2025-26/`, verbatim
snapshot), renamed `NN_Title.ipynb`; `22_Shor_Period_Finding_to_RSA.ipynb` is the companion of
`../lesson/`. The guided-reading apparatus (syntax comments, "🔧 Reading the code" tables,
"📐 Working it out" boxes, captioned drawings, "🔬 In-depth analysis" with reference solutions)
was added in this edition; the original text of the notebooks is preserved.
