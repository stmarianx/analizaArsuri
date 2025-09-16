import pandas as pd

print("1. Loading 'analize_filtrate.xlsx' ...")
df = pd.read_excel("analize_filtrate.xlsx")

# Ensure setdata is a date (not datetime)
print("2. Casting setdata to date ...")
df["setdata"] = pd.to_datetime(df["setdata"], errors="coerce").dt.date

# We keep ANANUME EXACT (no normalization, no symbol removal!)
if "ANANUME" not in df.columns:
    raise ValueError("Missing ANANUME column in analize_filtrate.xlsx")

# Prefer numeric value if available; fallback to raw rezval if needed
val_col = "valoare_numerica" if "valoare_numerica" in df.columns else "rezval"

print("3. Pivot to wide: one row per (precod, setdata), analyses as EXACT headers ...")
df_pivot = df.pivot_table(
    index=["precod","setdata"],
    columns="ANANUME",
    values=val_col,
    aggfunc="first"  # if multiple per day, keep first; adjust if client wants another rule
).reset_index()

print("4. Save 'analize_pe_zi.xlsx' with exact analysis names ...")
df_pivot.to_excel("analize_pe_zi.xlsx", index=False)

print("✅ 'analize_pe_zi.xlsx' generated with EXACT ANANUME headers (symbols kept).")
