# QC-Course — Quantum Computing Laboratory, edition 2026-27

Course notebooks organised by hardware ecosystem, plus a written lesson and a lecture deck on
RSA and Shor's algorithm. The notebooks are the "v2.2 enhanced" set of the 2025-26 course
(https://github.com/rcapp2506/QC-2025-26, Qiskit 2.x API), renumbered into a study path and
extended with a guided-reading apparatus.

## Layout

```
IBM/          the course notebooks on the IBM Qiskit stack (qiskit, qiskit-aer,
              qiskit-ibm-runtime), numbered in study order.
IQM/          the same notebooks re-backended for IQM Garnet (20q) & Emerald (54q) on
              IQM Resonance; shared helper iqm_backend.py + README.
lesson/       rsa_shor_lesson.tex (+ PDF) — a detailed lesson on RSA and Shor's algorithm,
              companion to 16_Shor_Period_Finding_to_RSA.ipynb;
              RSA_Shor_lecture.pptx — the lecture deck (MSc Physics); deck_src/ regenerates it.
qc-2025-26/   verbatim snapshot of the 2025-26 notebooks (the base of this edition).
archive/      an earlier, superseded upload of the course.
```

## Study path

Same numbering in `IBM/` and `IQM/`: `IBM/NN_x.ipynb` and `IQM/NN_x.ipynb` are the same notebook
on the two hardware stacks.

| # | notebook | what you learn |
|---|---|---|
| 01 | `01_Bloch_Sphere_Representation` | single-qubit states on the Bloch sphere, rotations, the three bases |
| 02 | `02_Construct_Circuits` | `QuantumCircuit`: registers, gates, composition, parameters, custom gates, execution, analysis |
| 03 | `03_Circuit_Library` | QFT, Grover operator, feature maps, ansätze, multi-controlled gates |
| 04 | `04_Operators` | circuits as unitaries, Pauli operators, observables and the Estimator |
| 05 | `05_Saving_to_Disk` | serialising circuits with QPY, metadata, good practices |
| 06 | `06_Aer_Noise_Simulation` | noise models: depolarising, T1/T2, readout; Grover under noise |
| 07 | `07_Running_on_Hardware` | accounts, backends, transpilation, jobs on a real device |
| 08 | `08_Teleportation` | entanglement, Bell measurement and classical corrections |
| 09 | `09_Simple_Deutsch_Jozsa` | the first quantum speed-up in one circuit |
| 10 | `10_Deutsch_Jozsa` | oracles, phase kickback, simulation and hardware, complexity |
| 11 | `11_Simple_Grover` | Grover's search on 2 and 3 qubits |
| 12 | `12_Quantum_Phase_Estimation` | QPE, precision, noise, iterative QPE |
| 13 | `13_RSA` | the classical target: keys, encryption, decryption, security |
| 14 | `14_Shor_Algorithm` | period finding with QPE, continued fractions, factoring 15 |
| 15 | `15_Shor_Algorithm_Generalized` | Shor for any small N with a permutation-matrix multiplier |
| 16 | `16_Shor_Period_Finding_to_RSA` | the complete, robust Shor pipeline up to breaking a toy RSA key — companion of `lesson/` |
| 17 | `17_PENNY-QUANV` | quantum machine learning: a quanvolutional layer (PennyLane + Keras) |

## Guided reading

Every notebook carries, in English: end-of-line comments on the main syntax, a
"🔧 Reading the code" table after every code cell, "📐 Working it out" boxes with the derivations
done by hand, circuit drawings (`draw()` helper around `qc.draw("mpl")`) with captions, and a
"🔬 In-depth analysis" with an empty cell and a reference solution.

## Quick start

**IBM / simulator (no account needed):**
```bash
pip install qiskit qiskit-aer matplotlib pandas pylatexenc
jupyter notebook IBM/16_Shor_Period_Finding_to_RSA.ipynb
```

**IQM Garnet/Emerald (IQM Resonance):**
```bash
pip install "qiskit-iqm>=18" matplotlib pandas pylatexenc
export IQM_TOKEN="<token from https://resonance.iqm.tech/>"
jupyter notebook IQM/16_Shor_Period_Finding_to_RSA.ipynb   # edit the single TARGET line to pick the backend
```
See `IQM/README.md` for the backend-selection table (local fake sim → cloud mock → real QPU).

## Highlights

- **`16_Shor_Period_Finding_to_RSA.ipynb`** (IBM and IQM) — an enriched, end-to-end Shor's
  algorithm: period finding → order→factor reduction → QPE circuit → continued fractions →
  a robust `shor_factor(N)` → breaking a toy RSA key.
- **`lesson/rsa_shor_lesson.tex`** — the theory behind it, with all theorems stated and
  explained, worked examples, and a step-by-step Shor recipe.
- **`lesson/RSA_Shor_lecture.pptx`** — a 30-slide lecture deck on the same material, with
  native (editable) equations and links to the demo notebooks.
