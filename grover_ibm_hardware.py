"""
grover_ibm_hardware.py
-----------------------
Runs Grover's algorithm on real IBM quantum hardware.
REQUIRES an IBM Quantum account — free at https://quantum.ibm.com

Steps:
    1. Create account at https://quantum.ibm.com
    2. Copy your API token from the dashboard
    3. Paste it into IBM_TOKEN below
    4. pip install qiskit qiskit-ibm-runtime qiskit-aer openpyxl pandas

Note: Jobs queue on IBM's servers — each run may take minutes to hours.
"""

import os
import numpy as np
import pandas as pd
import time
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IBM_TOKEN   = "YOUR_IBM_TOKEN_HERE"   # paste your token here
BACKEND_NAME = "ibm_kyiv"             # or ibm_brisbane, ibm_sherbrooke
SHOTS    = 1024
N_RUNS   = 10

def create_oracle(n, marked):
    oracle = QuantumCircuit(n)
    for i, bit in enumerate(reversed(marked)):
        if bit == '0':
            oracle.x(i)
    oracle.h(n - 1)
    oracle.mcx(list(range(n - 1)), n - 1)
    oracle.h(n - 1)
    for i, bit in enumerate(reversed(marked)):
        if bit == '0':
            oracle.x(i)
    return oracle

def diffuser(n):
    circuit = QuantumCircuit(n)
    circuit.h(range(n))
    circuit.x(range(n))
    circuit.h(n - 1)
    circuit.mcx(list(range(n - 1)), n - 1)
    circuit.h(n - 1)
    circuit.x(range(n))
    circuit.h(range(n))
    return circuit

def build_grover_circuit(n, marked):
    iterations = int(np.floor(np.pi / 4 * np.sqrt(2 ** n)))
    grover = QuantumCircuit(n)
    grover.h(range(n))
    for _ in range(iterations):
        grover.compose(create_oracle(n, marked), inplace=True)
        grover.compose(diffuser(n), inplace=True)
    grover.measure_all()
    return grover, iterations

def run_on_ibm(marked_states, n, shots=SHOTS, n_runs=N_RUNS):
    service = QiskitRuntimeService(token=IBM_TOKEN, channel="ibm_quantum")
    backend = service.backend(BACKEND_NAME)
    print(f"Using backend: {backend.name}")
    all_states = [format(i, f'0{n}b') for i in range(2 ** n)]

    for marked in marked_states:
        grover, iters = build_grover_circuit(n, marked)
        grover_t = transpile(grover, backend)
        print(f"\nn={n}, marked={marked}, iterations={iters}")
        df = pd.DataFrame(index=all_states)
        sampler = SamplerV2(mode=backend)

        for i in range(n_runs):
            print(f"  Submitting run {i+1}/{n_runs}...")
            job = sampler.run([grover_t], shots=shots)
            print(f"  Job ID: {job.job_id()}")
            while job.status() not in ["DONE", "ERROR", "CANCELLED"]:
                print(f"  Status: {job.status()} — waiting 10s...")
                time.sleep(10)
            if job.status() != "DONE":
                print(f"  Job {i+1} failed: {job.status()}")
                continue
            counts = job.result()[0].data.meas.get_counts()
            padded = {k.zfill(n): v for k, v in counts.items()}
            df[f'Run {i+1}'] = [padded.get(s, 0) for s in all_states]
            print(f"  Done. P(marked)={padded.get(marked, 0) / shots:.4f}")

        fname = os.path.join(SCRIPT_DIR, f"grover_IBM_{marked}.xlsx")
        df.to_excel(fname, index=True)
        print(f"  Saved: {fname}")

if __name__ == "__main__":
    # 3-qubit
    run_on_ibm(['000','001','010','011','100','101','110','111'], n=3)
    # 5-qubit (WARNING: very deep — expect high noise)
    # run_on_ibm(['11100', '00111'], n=5, shots=2048)
