"""
iqm_backend.py — shared helper for running the QC-Course notebooks on IQM hardware.

All IQM notebooks in this folder import `get_backend` and `run_counts` from here so
that the backend-selection logic lives in one place.  You can run every notebook in
three ways, controlled by a single string:

    target = "fake_apollo"   -> local noisy simulator, 20 qubits, NO token needed
    target = "fake_adonis"   -> local noisy simulator,  5 qubits, NO token needed
    target = "garnet:mock"   -> IQM Resonance CLOUD MOCK of Garnet  (needs token, no QPU time)
    target = "emerald:mock"  -> IQM Resonance CLOUD MOCK of Emerald (needs token, no QPU time)
                                NOTE: the :mock targets validate the whole job pipeline
                                (token, transpilation, connectivity, instruction limit) but
                                return RANDOM bitstrings, not simulated physics. Verify the
                                logic of a circuit with fake_apollo / fake_adonis instead.
    target = "garnet"        -> REAL Garnet  QPU (20 qubits) on IQM Resonance  (needs token + QPU credits)
    target = "emerald"       -> REAL Emerald QPU (54 qubits) on IQM Resonance  (needs token + QPU credits)

Garnet  : 20-qubit "Crystal" square-lattice chip. Native gates: PRX (phased-RX) + CZ.
Emerald : 54-qubit "Crystal" square-lattice chip. Native gates: PRX (phased-RX) + CZ.

Authentication
--------------
Get your API token from the IQM Resonance dashboard: https://resonance.iqm.tech/
Then EITHER export it once in your shell before launching Jupyter:

    export IQM_TOKEN="<your-resonance-token>"          # Linux / macOS
    $env:IQM_TOKEN = "<your-resonance-token>"          # Windows PowerShell

OR pass it explicitly:  get_backend("garnet", token="<your-resonance-token>")

Install the dependencies with:  pip install "qiskit-iqm>=18"
"""

from __future__ import annotations   # lets us write the type hint `str | None` on Python < 3.10
import os                            # environment variables (os.environ) for the token

RESONANCE_URL = "https://resonance.iqm.tech"
RESONANCE_MAX_INSTRUCTIONS = 10_000   # server-side cap per circuit (native instructions)


def get_backend(target: str = "fake_apollo", token: str | None = None):
    """Return an IQM Qiskit backend for the requested target (see module docstring).

    Syntax notes: `target: str = "fake_apollo"` is a type-hinted parameter with a default
    value; `token: str | None = None` means "a string, or None if not given".
    The `iqm.qiskit_iqm` imports are done inside the function (lazy imports) so that the
    module can be imported, and this error message shown, even if qiskit-iqm is missing.
    """
    # --- Local simulators: no network, no token ---------------------------------
    if target in ("fake_apollo", "fake_adonis"):
        from iqm.qiskit_iqm import IQMFakeApollo, IQMFakeAdonis
        return IQMFakeApollo() if target == "fake_apollo" else IQMFakeAdonis()

    # --- IQM Resonance (cloud mock OR real QPU) ---------------------------------
    from iqm.qiskit_iqm import IQMProvider
    # iqm-client reads the token from the IQM_TOKEN environment variable by itself and
    # refuses to receive it from BOTH a `token=` argument and the env var at the same time
    # ("Parameter sources must not be mixed"). So we funnel an explicit token into the
    # env var and never pass `token=` to IQMProvider.
    if token is not None:
        os.environ["IQM_TOKEN"] = token
    if not os.environ.get("IQM_TOKEN"):
        raise RuntimeError(
            f"target='{target}' needs an IQM Resonance token. Set the IQM_TOKEN "
            "environment variable or pass token=... . Get it from "
            "https://resonance.iqm.tech/ . For offline testing use "
            "target='fake_apollo' (no token required)."
        )
    provider = IQMProvider(RESONANCE_URL, quantum_computer=target)
    return provider.get_backend()


def run_counts(circuit, target_or_backend="fake_apollo", shots: int = 2048,
               optimization_level: int = 3, token: str | None = None,
               return_transpiled: bool = False):
    """Transpile `circuit` to the IQM native gate set and run it.

    `target_or_backend` may be a target string (see module docstring) or an already
    constructed backend object. Returns a Qiskit counts dict, or (counts, transpiled)
    if return_transpiled=True.
    """
    from iqm.qiskit_iqm import transpile_to_IQM

    backend = target_or_backend
    if isinstance(target_or_backend, str):           # a target name was given -> build the backend
        backend = get_backend(target_or_backend, token=token)

    transpiled = transpile_to_IQM(circuit, backend=backend,
                                  optimization_level=optimization_level)
    n_instr = transpiled.size()
    if n_instr > RESONANCE_MAX_INSTRUCTIONS:
        msg = (f"Transpiled circuit has {n_instr} native instructions; IQM Resonance declines "
               f"jobs with more than {RESONANCE_MAX_INSTRUCTIONS} instructions per circuit. "
               "Reduce the circuit (fewer qubits / shallower construction) before running it.")
        if "Fake" in type(backend).__name__:      # local simulator: no cap, but it will be SLOW
            import warnings
            warnings.warn(msg + " (running locally anyway)", stacklevel=2)
        else:
            raise RuntimeError(msg)
    job = backend.run(transpiled, shots=shots)
    result = job.result()
    # Cloud (Resonance) jobs do not raise on failure: they print the error and return an
    # empty Result. Surface the server's message instead of a confusing empty histogram.
    err = job.error_message() if hasattr(job, "error_message") else None
    if err:
        raise RuntimeError(f"IQM job failed: {err}")
    counts = result.get_counts()                     # dict {'bitstring': number of shots}
    return (counts, transpiled) if return_transpiled else counts   # conditional expression (ternary)
