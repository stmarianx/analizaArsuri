#!/usr/bin/env python3
"""
run_pipeline.py — orchestrator pentru pipeline-ul „Baza de Date – Marian”.

Rulează secvenţial cele şase script-uri; dacă un pas eşuează, execuţia se opreşte.
Toate fişierele (.py şi .xlsx) trebuie să fie în acelaşi folder cu acest script.

Utilizare:
    python run_pipeline.py                   # paşii 1-6
    python run_pipeline.py --skip-grafice    # sare pasul 5 (grafice)
    python run_pipeline.py --python venv\\Scripts\\python.exe   # alt interpret
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

# Ordinea paşilor (script, descriere)
PIPELINE = [
    ("procente_arsura.py",           "1 · Extrage procente şi curăţă TBSA"),
    ("pas2_prepare_master.py",       "2 · Construieşte master_lot.xlsx"),
    ("pas3_pivot_lot.py",            "3 · Pivot lot chirurgical"),
    ("build_baza_pacienti_finala.py","4 · Baza pacienţi finală"),
    ("grafic_pivot.py",              "5 · Grafice pivot & SVG"),
    ("scor_ABSI.py",                 "6 · Scor ABSI + audit final"),
]

def run(script: str, py_exec: str) -> None:
    """Rulează un script într-un sub-proces şi loghează durata."""
    logging.info("⇒ %s", script)
    start = time.perf_counter()
    try:
        subprocess.run([py_exec, script], check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("✖ %s a ieşit cu code %s", script, exc.returncode)
        sys.exit(exc.returncode)
    logging.info("✓ %s terminat în %.1fs", script, time.perf_counter() - start)

def main() -> None:
    parser = argparse.ArgumentParser(description="Rulează pipeline-ul cap-coadă.")
    parser.add_argument("--python", default=sys.executable,
                        help="Interpretul Python folosit (default: cel curent)")
    parser.add_argument("--skip-grafice", action="store_true",
                        help="Opreşte pasul 5 (grafice)")
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                        level=logging.INFO)

    steps = [p for p in PIPELINE if not (args.skip_grafice and p[0] == "grafic_pivot.py")]

    missing = [s for s, _ in steps if not Path(s).exists()]
    if missing:
        logging.error("Nu găsesc scripturile: %s", ", ".join(missing))
        sys.exit(1)

    logging.info("Pornesc pipeline-ul (Python=%s)…", args.python)
    for script, descr in steps:
        logging.info(descr)
        run(script, args.python)

    logging.info("🎉  Pipeline terminat cu succes!")

if __name__ == "__main__":
    main()
