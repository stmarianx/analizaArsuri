"""
build_baza_pacienti_finala.py
-----------------------------
Creeaza baza_pacienti_finala.xlsx (2997 pacienti, 1 rand per pacient).
"""

from pathlib import Path
import re
import pandas as pd

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def norm_str(s: str) -> str:
    """Upper + inlocuire spatii/simboluri cu _  (pentru nume col)."""
    return re.sub(r"[^\w]+", "_", str(s).strip().upper())

def extract_icd(text: str) -> str | None:
    """Extrage cod ICD (ex. T25.0)."""
    if pd.isna(text):
        return None
    m = re.search(r"[A-Z]\d{2}(?:\.\d+)?", str(text).upper())
    return m.group(0) if m else None

def split_multi(text: str) -> list[str]:
    if pd.isna(text) or not str(text).strip():
        return []
    return [t.strip() for t in re.split(r"[;,/+\|]", str(text)) if t.strip()]

# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------

df_p = pd.read_excel(Path("pacienti_cu_procente.xlsx"))
df_m = pd.read_excel(Path("master_lot.xlsx"))

# ------------------------------------------------------------------
# Merge + keep cauze + grad
# ------------------------------------------------------------------

cause_cols = [c for c in df_m.columns if c.lower() in
              ["flacara", "lichid", "contact", "chimica",
               "electrica", "solara", "explozie"]]

grad_cols = ["GRAD_I", "GRAD_II", "GRAD_IIA", "GRAD_IIB", "GRAD_III", "GRAD_IV"]

df_m_small = df_m[["precod"] + cause_cols + grad_cols]
df = df_p.merge(df_m_small, on="precod", how="left")

# ------------------------------------------------------------------
# Bazic (sex/mediu 0-1, ZILE_SPITAL)
# ------------------------------------------------------------------

df["SEX"]   = df["SEX"].str.upper().map({"F": 0, "M": 1})
df["MEDIU"] = df["MEDIU"].str.upper().map({"U": 0, "R": 1})

df["DATA_INTERNARE"] = pd.to_datetime(df["DATA_INTERNARE"], errors="coerce")
df["DATA_EXTERNARE"] = pd.to_datetime(df["DATA_EXTERNARE"], errors="coerce")
df["ZILE_SPITAL"] = (df["DATA_EXTERNARE"] - df["DATA_INTERNARE"]).dt.days
df.drop(columns=["DATA_INTERNARE", "DATA_EXTERNARE"], inplace=True)

# ------------------------------------------------------------------
# TIP_INTERNARE & STARE_EXTERNARE  (one-hot 0/1)
# ------------------------------------------------------------------

tip_vals = (
    df_p["TIP_INTERNARE"].fillna("UNKNOWN")
    .str.upper().str.replace(r"\s+", "_", regex=True)
    .unique()
)
stare_vals = (
    df_p["STARE_EXTERNARE"].fillna("UNKNOWN")
    .str.upper().str.replace(r"\s+", "_", regex=True)
    .unique()
)

df_tip = pd.get_dummies(
    df["TIP_INTERNARE"].fillna("UNKNOWN")
      .str.upper().str.replace(r"\s+", "_", regex=True),
    dtype=int
)
df_stare = pd.get_dummies(
    df["STARE_EXTERNARE"].fillna("UNKNOWN")
      .str.upper().str.replace(r"\s+", "_", regex=True),
    dtype=int
)

df = pd.concat(
    [df.drop(columns=["TIP_INTERNARE", "STARE_EXTERNARE"]), df_tip, df_stare],
    axis=1
)

# ------------------------------------------------------------------
# ICD one-hot
# ------------------------------------------------------------------

df["ICD_CODE"] = df["DIAG_PRINCIPAL"].apply(extract_icd)
icd_dummy = pd.get_dummies(
    df["ICD_CODE"].fillna("UNKNOWN").str.replace(".", "_", regex=False),
    prefix="", prefix_sep="", dtype=int
)
icd_cols = sorted(icd_dummy.columns)
df = pd.concat([df.drop(columns=["DIAG_PRINCIPAL", "ICD_CODE"]), icd_dummy], axis=1)

# ------------------------------------------------------------------
# Interventii one-hot (fara prefix INT_)
# ------------------------------------------------------------------

pat_code = re.compile(r"[A-Z]\d{4,5}-\d{2}")

def int_key(txt):
    if pd.isna(txt):
        return None
    up = str(txt).upper()
    m  = pat_code.search(up)
    if m:
        return m.group(0).replace("-", "_")   # doar codul
    return norm_str(up)[:30]

codes = df["INTERVENTIE_CHIRURGICALA"].apply(int_key)
codes_expl = codes.apply(lambda x: [x] if x else []).explode()

dummy_int = (
    pd.crosstab(codes_expl.index, codes_expl)   # ← fara dtype
      .astype(int)                              # convertim la 0/1
      .reindex(df.index, fill_value=0)
)
interv_cols = sorted(dummy_int.columns)

df = (
    df.drop(columns=["INTERVENTIE_CHIRURGICALA", "COD_INTERVENTIE"], errors="ignore")
      .join(dummy_int)
)

# ------------------------------------------------------------------
# ------------------------------------------------------------------
# GRAD (preluat din master_lot) 0/1 - deja one-hot, nimic de calculat
# ------------------------------------------------------------------

# grad_cols already selected from master_lot merge; values are 0/1 integers

# Drop raw text cols nefolosite
# ------------------------------------------------------------------

df.drop(columns=[
    "DIAG_PRINCIPAL_NORMALIZAT", "TIP_EXTERNARE",
    "mednume", "DIAG_SECUNDARE", "DIAGNOSTICE",
    "EPICRIZA", "ati", "DATA_INTERVENTIE"
], errors="ignore", inplace=True)

# ------------------------------------------------------------------
# Boolean -> int (safety)
# ------------------------------------------------------------------

bool_cols = df.select_dtypes(include="bool").columns
df[bool_cols] = df[bool_cols].astype(int)

# ------------------------------------------------------------------
# Order columns
# ------------------------------------------------------------------

base_cols = ["an", "SECTIE", "precod", "FO", "PACIENT", "DATA_NASTERE",
             "SEX", "VARSTA", "MEDIU"]

tip_cols   = [c for c in tip_vals   if c in df.columns]
stare_cols = [c for c in stare_vals if c in df.columns]
mid_cols   = ["ZILE_SPITAL", "PROCENT_SUPRAF_ARS"]

cause_cols_sorted = sorted(cause_cols)

rest_cols = sorted([c for c in df.columns
                    if c not in (base_cols + tip_cols + stare_cols +
                                 mid_cols + grad_cols + cause_cols_sorted +
                                 icd_cols + interv_cols)])

df = df[base_cols + tip_cols + stare_cols + mid_cols +
        grad_cols + cause_cols_sorted + icd_cols + interv_cols + rest_cols]

# ------------------------------------------------------------------
# Validate
# ------------------------------------------------------------------

assert df["precod"].nunique() == 2997, "precod duplicat / lipsa"
assert df["SEX"].notna().all() and df["MEDIU"].notna().all()

# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------

out = "baza_pacienti_finala.xlsx"
with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="pacienti", index=False)
    pd.DataFrame({"column": df.columns}).to_excel(writer, sheet_name="codebook", index=False)

print("Done!  Rows:", df.shape[0], "Cols:", df.shape[1])
df = pd.read_excel("baza_pacienti_finala.xlsx", sheet_name="pacienti")
print(df[["GRAD_I", "GRAD_II", "GRAD_IIA", "GRAD_IIB", "GRAD_III", "GRAD_IV"]].sum())