import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Setare stil
sns.set(style="whitegrid")
plt.rcParams["axes.labelsize"] = 10

# 1. Încărcare fișiere
df_procente = pd.read_excel("pacienti_cu_procente.xlsx", usecols=["precod", "DATA_INTERNARE", "DATA_EXTERNARE"])
df_cauze = pd.read_excel("cauze_arsuri.xlsx")

# 2. Calcul durata spitalizare per pacient
df_procente["DATA_INTERNARE"] = pd.to_datetime(df_procente["DATA_INTERNARE"], errors="coerce")
df_procente["DATA_EXTERNARE"] = pd.to_datetime(df_procente["DATA_EXTERNARE"], errors="coerce")
df_procente["ZILE_SPITAL"] = (df_procente["DATA_EXTERNARE"] - df_procente["DATA_INTERNARE"]).dt.days

df_unique = df_procente[["precod", "ZILE_SPITAL"]].dropna().drop_duplicates("precod")

# 3. Adăugare cauză dominantă
df = df_unique.merge(df_cauze, on="precod", how="left")
cauze = ['flacara', 'lichid', 'contact', 'electrocutie', 'chimica', 'solara', 'explozie']
df["CAUZA_DOMINANTA"] = df[cauze].idxmax(axis=1)
df = df[df["ZILE_SPITAL"].notna() & df["CAUZA_DOMINANTA"].notna()]

# 4. Pregătire grafic
plt.figure(figsize=(12, 6))
sns.violinplot(data=df, x="CAUZA_DOMINANTA", y="ZILE_SPITAL", inner="box", palette="Set2")

# Adăugare n=... sub fiecare violină
n_counts = df.groupby("CAUZA_DOMINANTA")["precod"].count()
for i, (label, n) in enumerate(zip(n_counts.index, n_counts)):
    plt.text(i, -5, f"n={n}", ha="center", va="top", fontsize=10)

plt.ylim(bottom=-10)
plt.title("Distribuția duratei spitalizării în funcție de cauza arsurii")
plt.xlabel("Cauza arsurii")
plt.ylabel("Zile de spitalizare")

plt.tight_layout()
plt.savefig("violinplot_durata_pe_cauza.svg", format="svg")
plt.savefig("violinplot_durata_pe_cauza.png", dpi=300)

