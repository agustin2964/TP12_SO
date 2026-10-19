#!/usr/bin/env python3
"""Harness de prueba: ejecuta A y B para cada protocolo y muestra la salida."""
import subprocess
import sys
import time

PROTOCOLS = ["2", "3", "4"]

for proto in PROTOCOLS:
    print("=" * 60)
    print(f"PROTOCOLO DE {proto} VIAS")
    print("=" * 60)

    # B (respondedor) debe arrancar primero
    p_b = subprocess.Popen(
        [sys.executable, "protocolo.py", "B", proto],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    time.sleep(0.5)
    p_a = subprocess.Popen(
        [sys.executable, "protocolo.py", "A", proto],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    try:
        out_a, _ = p_a.communicate(timeout=15)
        out_b, _ = p_b.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        p_a.kill()
        p_b.kill()
        out_a = "(timeout A)"
        out_b = "(timeout B)"

    print("--- Salida de A (iniciador) ---")
    print(out_a or "(vacia)")
    print("--- Salida de B (respondedor) ---")
    print(out_b or "(vacia)")
    print()

print("Pruebas finalizadas.")
