import pandas as pd

# Încarcă fișierele (dacă nu ai deja în script)
df_procente = pd.read_excel("pacienti_cu_procente.xlsx", usecols=["precod", "DATA_INTERNARE", "DATA_EXTERNARE"])
df_cauze = pd.read_excel("cauze_arsuri.xlsx")

# Calcul durată spitalizare
df_procente["DATA_INTERNARE"] = pd.to_datetime(df_procente["DATA_INTERNARE"], errors="coerce")
df_procente["DATA_EXTERNARE"] = pd.to_datetime(df_procente["DATA_EXTERNARE"], errors="coerce")
df_procente["ZILE_SPITAL"] = (df_procente["DATA_EXTERNARE"] - df_procente["DATA_INTERNARE"]).dt.days

df_unique = df_procente[["precod", "ZILE_SPITAL"]].dropna().drop_duplicates("precod")
df = df_unique.merge(df_cauze, on="precod", how="left")

# Determinare cauza dominantă
cauze = ['flacara', 'lichid', 'contact', 'electrocutie', 'chimica', 'solara', 'explozie']
df["CAUZA_DOMINANTA"] = df[cauze].idxmax(axis=1)

# Filtrare pentru "flacara"
df_flacara = df[df["CAUZA_DOMINANTA"] == "flacara"]

# Calcul IQR pentru boxplot
q1 = df_flacara["ZILE_SPITAL"].quantile(0.25)
q3 = df_flacara["ZILE_SPITAL"].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

# Identificare outlieri
outliers = df_flacara[df_flacara["ZILE_SPITAL"] > upper_bound]

# Afișare rezultate
print(f"Total pacienți cu arsuri prin flacără: {len(df_flacara)}")
print(f"Număr de outlieri: {len(outliers)}")
print("Zile de spitalizare (outlieri):")
print(outliers["ZILE_SPITAL"].sort_values().tolist())
