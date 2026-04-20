"""
grover_ideal_correct.py
-----------------------
Generates ideal Grover's algorithm data using the correct n-qubit oracle.
Runs entirely on the local QASM simulator — no IBM account needed.

Output files are saved in the same directory as this script.

Requirements:
    pip install qiskit qiskit-aer openpyxl pandas

Usage:
    python grover_ideal_correct.py
"""

import os
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# ── Save directory = same folder as this script ───────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_oracle(n, marked):
    """
    Phase oracle: flips sign of marked state using multi-controlled-Z.
    Correct for any n and any marked state.
    """
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
    """Grover diffusion operator: 2|psi><psi| - I"""
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

def run_grover_ideal(n, marked_states, shots, n_runs=10, seed=42):
    sim = AerSimulator()
    results = {}
    for marked in marked_states:
        grover, iters = build_grover_circuit(n, marked)
        t = transpile(grover, sim)
        print(f"n={n}, marked={marked}, iterations={iters}")
        run_data = {}
        for r in range(1, n_runs + 1):
            counts = sim.run(t, shots=shots, seed_simulator=seed + r).result().get_counts()
            print(f"  Run {r}: P(marked)={counts.get(marked, 0) / shots:.4f}")
            run_data[r] = counts
        results[marked] = run_data
    return results

def save_to_excel(results, n, prefix="grover_ideal"):
    all_states = [format(i, f'0{n}b') for i in range(2 ** n)]
    for marked, run_data in results.items():
        df = pd.DataFrame(index=all_states)
        for r, counts in run_data.items():
            df[f'Run {r}'] = [counts.get(s, 0) for s in all_states]
        fname = os.path.join(SCRIPT_DIR, f"{prefix}_{marked}.xlsx")
        df.to_excel(fname, index=True)
        print(f"Saved: {fname}")

if __name__ == "__main__":
    # 3-qubit: all 8 states, 1024 shots
    res3 = run_grover_ideal(3, ['000','001','010','011','100','101','110','111'], shots=1024)
    save_to_excel(res3, n=3)

    # 4-qubit: first 10 states, 1024 shots
    res4 = run_grover_ideal(4, ['0000','0001','0010','0011','0100',
                                '0101','0110','0111','1000','1001'], shots=1024)
    save_to_excel(res4, n=4)

    # 5-qubit: two alternating states (as in paper), 2048 shots
    res5 = run_grover_ideal(5, ['11100','00111'], shots=2048)
    save_to_excel(res5, n=5)

    print("\nDone.")
