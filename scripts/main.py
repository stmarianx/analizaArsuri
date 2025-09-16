import pandas as pd
import re
import unicodedata

# Optional: keep, though we no longer use it for filtering
def normalize(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn').lower()

SRC = "CONFIDENTIAL.xlsx"

# 1) Load sheets
df_pacienti = pd.read_excel(SRC, sheet_name="pacienti", engine="openpyxl")
df_analize  = pd.read_excel(SRC, sheet_name="analize",  engine="openpyxl")

# 2) KEEP ALL PATIENTS (no filtering by 'ars')
df_pacienti_filtrat = df_pacienti.copy()

# 3) Extract numeric value and H/L tag from 'rezval' (non-destructive)
def extrage_valoare_si_eticheta(raw):
    if pd.isna(raw):
        return pd.Series([None, None])
    text = str(raw).strip()
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)([A-Za-z]*)", text)
    if m:
        try:
            valoare = float(m.group(1))
        except ValueError:
            valoare = None
        eticheta = m.group(2).upper() if m.lastindex and m.group(2) else None
        return pd.Series([valoare, eticheta])
    return pd.Series([None, None])

df_analize[["valoare_numerica", "eticheta"]] = df_analize["rezval"].apply(extrage_valoare_si_eticheta)

# 4) Keep only analyses for patients in the lot (which is effectively all)
coduri_validi = df_pacienti_filtrat["precod"].dropna().unique()
df_analize_filtrat = df_analize[df_analize["precod"].isin(coduri_validi)].copy()

# 5) (Optional) ensure 'setdata' is a date (helps the next pivot step)
if "setdata" in df_analize_filtrat.columns:
    df_analize_filtrat["setdata"] = pd.to_datetime(df_analize_filtrat["setdata"], errors="coerce").dt.date

# 6) Save intermediates with expected names for downstream scripts
df_pacienti_filtrat.to_excel("pacienti_filtrati.xlsx", index=False)
df_analize_filtrat.to_excel("analize_filtrate.xlsx", index=False)

print("✅ Saved: pacienti_filtrati.xlsx & analize_filtrate.xlsx (all patients kept, ANANUME untouched).")
