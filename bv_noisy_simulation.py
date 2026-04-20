"""
bv_noisy_simulation.py
-----------------------
Runs the Bernstein-Vazirani algorithm on:
  (a) Ideal QASM simulator
  (b) FakeBrisbane noise model — uses real ibm_brisbane calibration data
      (gate error rates, T1/T2 times). Runs locally, NO IBM account needed.

Output files are saved in the same directory as this script.

Requirements:
    pip install qiskit qiskit-aer qiskit-ibm-runtime openpyxl pandas numpy
"""

import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeBrisbane

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def bv_circuit(n, secret):
    """
    Bernstein-Vazirani circuit for secret string of length n.
    Ideal output: always the secret string with P=1.0.
    """
    qc = QuantumCircuit(n + 1, n)   # n query qubits + 1 ancilla
    qc.x(n)                          # ancilla |0> -> |1>
    qc.h(n)                          # ancilla |1> -> |->
    qc.h(range(n))                   # query qubits into superposition
    for i, bit in enumerate(reversed(secret)):
        if bit == '1':
            qc.cx(i, n)              # CNOT for each '1' in secret
    qc.h(range(n))                   # inverse Hadamard
    qc.measure(range(n), range(n))
    return qc

def get_prob_vec(counts, all_states):
    arr = np.array([counts.get(s, 0) for s in all_states], dtype=float)
    total = arr.sum()
    return arr / total if total > 0 else arr

def compute_all_measures(ideal_p, noisy_p):
    n = len(ideal_p)
    diff = ideal_p - noisy_p
    m1 = 1 - np.sum(np.abs(diff)) / n
    m2 = 1 - np.sqrt(np.sum(diff**2)) / np.sqrt(n)
    denom = np.linalg.norm(ideal_p) * np.linalg.norm(noisy_p)
    m3 = float(np.dot(ideal_p, noisy_p) / denom) if denom > 0 else 0.0
    m4 = 1 - float(np.max(np.abs(diff)))
    m5 = 1 - float((np.sum(diff**2) / n) ** 0.5)
    return m1, m2, m3, m4, m5

def run_bv_experiment(secrets, shots, n_runs=10, seed=42):
    n = len(secrets[0])
    all_states = [format(i, f'0{n}b') for i in range(2 ** n)]

    ideal_sim = AerSimulator()
    noise_model = NoiseModel.from_backend(FakeBrisbane())
    noisy_sim = AerSimulator(noise_model=noise_model)

    rows = []
    print(f"\n{n}-qubit BV (FakeBrisbane noise model, {shots} shots):")
    print(f"{'Exec':>4} {'Secret':>7} {'M1':>8} {'M2':>8} {'M3':>8} {'M4':>8} {'M5':>8} | P(correct)")

    for i, secret in enumerate(secrets):
        qc = bv_circuit(n, secret)
        ideal_c = ideal_sim.run(
            transpile(qc, ideal_sim), shots=shots, seed_simulator=seed + i
        ).result().get_counts()
        noisy_c = noisy_sim.run(
            transpile(qc, noisy_sim), shots=shots, seed_simulator=seed + i
        ).result().get_counts()

        ip = get_prob_vec(ideal_c, all_states)
        bp = get_prob_vec(noisy_c, all_states)
        m1, m2, m3, m4, m5 = compute_all_measures(ip, bp)
        p_correct = noisy_c.get(secret, 0) / shots

        print(f"{i+1:>4} {secret:>7} {m1:>8.4f} {m2:>8.4f} "
              f"{m3:>8.4f} {m4:>8.4f} {m5:>8.4f} | {p_correct:.4f}")
        rows.append({'Execution': i+1, 'Secret': secret,
                     'M1': round(m1,4), 'M2': round(m2,4), 'M3': round(m3,4),
                     'M4': round(m4,4), 'M5': round(m5,4), 'P_correct': round(p_correct,4)})

    df = pd.DataFrame(rows)
    print(f"\n{'Mean':>12}", end="")
    for col in ['M1','M2','M3','M4','M5']:
        print(f" {df[col].mean():>8.4f}", end="")
    print(f"\n{'SD':>12}", end="")
    for col in ['M1','M2','M3','M4','M5']:
        print(f" {df[col].std():>8.4f}", end="")
    print(f"\nMean P(correct): {df['P_correct'].mean():.4f}")

    fname = os.path.join(SCRIPT_DIR, f"bv_results_{n}qubit.xlsx")
    df.to_excel(fname, index=False)
    print(f"Saved: {fname}")
    return df

if __name__ == "__main__":
    run_bv_experiment(['000','001','010','011','100','101','110','111','000','001'], shots=1024)
    run_bv_experiment(['0000','0001','0010','0011','0100','0101','0110','0111','1000','1001'], shots=1024)
    run_bv_experiment(['11100','00111','00111','11100','00111',
                       '11100','00111','11100','00111','11100'], shots=2048)
