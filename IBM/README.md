# QC-Course — IBM edition

These are the original course notebooks, targeting the **IBM Qiskit** stack
(`qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`). The parallel `../IQM` folder contains
the same notebooks re-backended for IQM Garnet/Emerald on IQM Resonance.

## Setup

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime matplotlib pandas
```

Most notebooks run entirely on the local `AerSimulator`, so no account is needed.
To run on real IBM hardware, see `running_on_hardware.ipynb`.

## Fixes applied in this folder

- **Retired `channel="ibm_quantum"`** → updated to `channel="ibm_quantum_platform"`
  in `grovers-algorithm.ipynb`, `New Deutsch - Jozsa.ipynb`, and
  `running_on_hardware.ipynb`. The legacy `ibm_quantum` channel (with
  `instance="ibm-q/open/main"`) was sunset in 2025; accounts now authenticate against
  the IBM Quantum Platform on IBM Cloud with a token from
  https://quantum.cloud.ibm.com/ .

Everything else is preserved as in the upstream course material.
