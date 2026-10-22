# QC-Course — IQM edition (Garnet & Emerald on IQM Resonance)

This folder is a port of the course notebooks to **IQM** superconducting quantum
computers, runnable on the **IQM Resonance** cloud (`https://resonance.iqm.tech/`).
The `../IBM` folder keeps the original IBM-Qiskit-Runtime versions.

## What changed vs. the IBM notebooks

| IBM version | IQM version |
|---|---|
| `AerSimulator()` / `generate_preset_pass_manager(3, AerSimulator())` | `iqm_backend.get_backend(...)` + `transpile_to_IQM(...)` |
| `qiskit_ibm_runtime.QiskitRuntimeService` / `SamplerV2` | `iqm.qiskit_iqm.IQMProvider` + `backend.run(...)` |
| IBM heavy-hex topology, native basis `{ECR, RZ, SX, X}` | IQM **Crystal** square lattice, native basis **`{PRX, CZ}`** |

The physics and the circuits are identical — only the backend, the transpilation
target, and the native gate set differ.

## The two machines

| Device | Qubits | Topology | Native gates |
|---|---|---|---|
| **Garnet**  | 20 | Crystal (square lattice) | PRX (phased-RX), CZ |
| **Emerald** | 54 | Crystal (square lattice) | PRX (phased-RX), CZ |

## Setup

```bash
pip install "qiskit-iqm>=18"
export IQM_TOKEN="<your-resonance-token>"     # from https://resonance.iqm.tech/
# Windows PowerShell:  $env:IQM_TOKEN = "<your-resonance-token>"
```

## How to pick where a notebook runs

Every notebook has a single configuration line near the top:

```python
from iqm_backend import get_backend, run_counts
TARGET = "fake_apollo"     # change this one line to choose the backend
```

| `TARGET` value | Runs on | Token? | QPU credits? |
|---|---|---|---|
| `"fake_apollo"`  | local 20-qubit noisy simulator | no  | no  |
| `"fake_adonis"`  | local 5-qubit noisy simulator  | no  | no  |
| `"garnet:mock"`  | cloud mock of Garnet (random bitstrings, pipeline check only) | yes | no  |
| `"emerald:mock"` | cloud mock of Emerald (random bitstrings, pipeline check only) | yes | no  |
| `"garnet"`       | **real Garnet QPU** (20q)      | yes | yes |
| `"emerald"`      | **real Emerald QPU** (54q)     | yes | yes |

Develop and validate logic with `"fake_apollo"` (free, offline, noisy physics simulation).
Use `"garnet:mock"` to check the cloud pipeline end to end (token, transpilation to the
live calibration set, instruction limit, job submission) — but note that the `:mock`
targets return **random bitstrings**, not simulated outcomes (a Bell circuit gives all four
results with equal weight). Then switch to `"garnet"` / `"emerald"` for a real run.

## Running a circuit (the one pattern used everywhere)

```python
from iqm_backend import run_counts
counts = run_counts(qc, TARGET, shots=2048)       # transpiles + runs + returns counts
plot_histogram(counts)
```

or, if you need the backend object (e.g. to inspect the coupling map):

```python
from iqm_backend import get_backend
from iqm.qiskit_iqm import transpile_to_IQM
backend = get_backend(TARGET)
tqc = transpile_to_IQM(qc, backend=backend, optimization_level=3)
counts = backend.run(tqc, shots=2048).result().get_counts()
```

## Notebooks ported

Fully re-backended to IQM (build → transpile to PRX/CZ → run on Garnet/Emerald):

- `Deutsch-Algorithm.ipynb`
- `New Deutsch - Jozsa.ipynb`
- `grover.ipynb`, `grovers-algorithm.ipynb`, `simple_grover.ipynb`
- `quantum phase estimation.ipynb`
- `period_finding_and_shor.ipynb`, `shor.ipynb`
- `teleportation.ipynb`
- `running_on_hardware.ipynb` (IQM Resonance connection guide)

Framework-neutral construction notebooks (`operators`, `measurement`,
`circuit-library`, `construct-circuits`, `Classical feedforward and control flow`,
`saving_to_disk`) build Qiskit circuits that are already backend-agnostic; they carry
an IQM header cell explaining how to run them on Garnet/Emerald with the helper above.

> **Note on circuit size.** IQM Resonance declines any job whose transpiled circuit has
> more than **10 000 native instructions** (`run_counts` checks this and raises before
> submitting). The Shor notebooks therefore compute $a^{2^q} \bmod 15$ classically and
> apply one controlled multiplication per counting qubit (~650 native instructions),
> instead of repeating $U$ $2^q$ times (~70 000).
>
> **Note on qubit counts.** Shor/QPE with 8 counting qubits use 12 qubits — fine on
> Garnet (20) and Emerald (54). Deep circuits like Shor will be noisy on today's
> hardware; use `fake_apollo` to verify logic, and expect the characteristic
> spreading of the measured-phase histogram on the real QPU.
