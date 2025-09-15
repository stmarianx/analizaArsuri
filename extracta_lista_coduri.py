"""
extracta_lista_coduri.py
------------------------
Genereaza doua fisiere Excel cu:
  1) Lista coduri ICD principale unice
  2) Lista interventii chirurgicale unice

Input: pacienti_cu_procente.xlsx
"""

import re
import pandas as pd
from pathlib import Path

SRC = Path("pacienti_cu_procente.xlsx")

# ------------------------------------------------------------------
# Incarcare sursa
# ------------------------------------------------------------------
df = pd.read_excel(SRC, usecols=["DIAG_PRINCIPAL", "INTERVENTIE_CHIRURGICALA"])

# ------------------------------------------------------------------
# Lista unica DIAG_PRINCIPAL (cod ICD + text brut)
# ------------------------------------------------------------------
def extract_icd(text):
    if pd.isna(text):
        return None
    m = re.search(r"[A-Z]\d{2}(?:\.\d+)?", str(text).upper())
    return m.group(0) if m else None

df_diag = (
    df["DIAG_PRINCIPAL"]
      .dropna()
      .unique()
)

# tabel cu cod + text complet
diag_rows = []
for raw in df_diag:
    icd = extract_icd(raw)
    diag_rows.append({"ICD": icd, "DIAG_PRINCIPAL_RAW": raw})

pd.DataFrame(diag_rows).sort_values(["ICD", "DIAG_PRINCIPAL_RAW"]) \
    .to_excel("diagnostice_principale_unice.xlsx", index=False)

print("Salvat => diagnostice_principale_unice.xlsx")

# ------------------------------------------------------------------
# Lista unica INTERVENTIE_CHIRURGICALA (cod + descriere)
# ------------------------------------------------------------------
def int_key(raw):
    if pd.isna(raw):
        return None
    raw_u = str(raw).upper()
    m = re.search(r"[A-Z]\d{4,5}-\d{2}", raw_u)
    return m.group(0) if m else None     # cod sau None

interv_unique = df["INTERVENTIE_CHIRURGICALA"].dropna().unique()

int_rows = []
for raw in interv_unique:
    cod = int_key(raw)
    int_rows.append({"COD": cod, "INTERVENTIE_RAW": raw})

pd.DataFrame(int_rows).sort_values(["COD", "INTERVENTIE_RAW"]) \
    .to_excel("interventii_chirurgicale_unice.xlsx", index=False)

print("Salvat => interventii_chirurgicale_unice.xlsx")
