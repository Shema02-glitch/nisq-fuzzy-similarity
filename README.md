# nisq-fuzzy-similarity

## What this is


This repository contains the experimental code used to compare five normalised fuzzy similarity measures — Hamming (M1), Euclidean (M2), Cosine (M3), Hausdorff (M4), Minkowski (M5) — applied to quantum output distributions from Grover's algorithm and the Bernstein-Vazirani (BV) algorithm, run on both ideal simulators and real IBM quantum hardware.
The central finding is that the Cosine measure (M3) tracks decoherence severity across qubit scales in a way the other measures do not: it stays high when hardware preserves Grover's amplitude amplification (n=3), becomes highly variable under partial decoherence (n=4), and collapses to the theoretical floor 1/√(2ⁿ) when noise completely overwhelms the circuit (n=5). M1 (Hamming) remains stable throughout and misses the transition entirely.
Hardware used: ibm_kyiv (Grover's), ibm_brisbane (BV, n=4 and n=5).

Repository structure
- grover_ideal_correct.py         - Ideal Grover simulation using correct n-qubit oracle
- grover_ibm_hardware.py          - Grover's on real IBM hardware (requires API token)
- bv_noisy_simulation.py          - BV on ideal + FakeBrisbane noise model (no token needed)
- compute_similarity_measures.py  - Computes all five measures from Excel data files

## Scripts
### grover_ideal_correct.py
Generates ideal Grover's algorithm data using a correct n-qubit phase oracle (multi-controlled-X sandwiched by Hadamards). Runs entirely on the local QASM simulator — no IBM account needed. Saves results as Excel files, one per marked state.
The earlier version of this experiment used a hardcoded cz(0,1) gate regardless of qubit count or marked state, which produced uniformly random output and invalidated the original comparisons. This script uses the correct construction.
### grover_ibm_hardware.py
Submits Grover circuits to real IBM quantum hardware via the Qiskit Runtime Sampler. Requires an IBM Quantum account and API token (free at quantum.ibm.com). Polls for job completion and saves results as Excel files. The IBM hardware data used in the paper was collected from ibm_kyiv.
### bv_noisy_simulation.py
Runs the Bernstein-Vazirani algorithm on:

The ideal QASM simulator (always P(correct) = 1.0)
The FakeBrisbane noise model, which uses real ibm_brisbane calibration data (gate error rates, T1/T2 decoherence times) to simulate hardware noise locally

No IBM account needed for FakeBrisbane. Results are physics-grounded but not identical to real hardware runs — this distinction is noted in the paper.
### compute_similarity_measures.py
Takes the Excel output files from the above scripts and computes all five fuzzy similarity measures, prints statistics tables (mean, SD, min, max), and runs one-sample t-tests against a threshold. This is the analysis layer, separate from data collection.

## Installation
bashpip install qiskit, qiskit-aer, qiskit-ibm-runtime, openpyxl, numpy, scipy, and pandas

Tested with:
qiskit 2.0.0,
qiskit-aer 0.15.1,
qiskit-ibm-runtime 0.37.0, and
Python 3.11


## Reproducing the results
Ideal Grover data (no IBM account needed):
bashpython grover_ideal_correct.py
This generates grover_ideal_<state>.xlsx for each marked state.

IBM hardware data:
Paste your IBM Quantum API token into grover_ibm_hardware.py and run:
bashpython grover_ibm_hardware.py
Note: 5-qubit Grover circuits are deep enough that real hardware results will be essentially uniform due to decoherence — this is a finding of the paper, not a bug.

BV simulation (no IBM account needed):
bashpython bv_noisy_simulation.py

Compute similarity measures:
Place ideal and IBM Excel files in the same directory, then:
bashpython compute_similarity_measures.py

## Key result
M3 (Cosine similarity) satisfies a closed-form lower bound under complete decoherence:
M3(ideal, uniform_hardware) ≈ 1/√(2ⁿ)

For n=5: 1/√32 ≈ 0.177, consistent with the observed mean M3 = 0.192 on ibm_kyiv.

This makes M3 a practical indicator of whether a quantum circuit's output structure has survived the hardware — something M1 (Hamming) cannot detect.
