import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
from scipy.stats import kruskal, chi2_contingency
import numpy as np, matplotlib as mpl, warnings

sns.set(style="whitegrid"); mpl.rcParams["font.size"] = 10
warnings.filterwarnings("ignore", category=UserWarning)        # ascunde set_ticklabels & tight

df = pd.read_excel("pivot_arsuri_lot.xlsx")

cauze_de_afisat = ['flacara','lichid','contact','electrocutie','chimica','solara','explozie']
df = df[df['CAUZA_DOMINANTA'].isin(cauze_de_afisat)].copy()

# -------- HEATMAP ----------------------------------------------------------
pivot_mean  = df.pivot_table(index='CAUZA_DOMINANTA', columns='PROCENT_INTERVAL',
                             values='ZILE_SPITAL_MEDIE')
pivot_count = df.pivot_table(index='CAUZA_DOMINANTA', columns='PROCENT_INTERVAL',
                             values='NR_PACIENTI', aggfunc='sum').fillna(0).astype(int)
annot = pivot_mean.round(1).astype(str) + "\n(n=" + pivot_count.astype(str) + ")"

plt.figure(figsize=(10,6))
sns.heatmap(pivot_mean, annot=annot, fmt='', cmap="YlOrRd",
            linewidths=.5, linecolor='grey')
plt.title("Durata medie a spitalizării\nîn funcție de cauza și suprafața arsă")
plt.ylabel("Cauza arsurii"); plt.xlabel("Procent suprafață arsă")
plt.tight_layout(); plt.savefig("grafic_pivot_arsuri.svg")
print("✅ grafic_pivot_arsuri.svg salvat")

# -------- BOXPLOT PRO – limita 100 zile, exclude n=0 -----------------------------

sns.set_theme(style="whitegrid", font_scale=1.1)          # fonturi + stil
plt.rcParams["axes.linewidth"] = 0.8                      # contur fin grafic

# 1) Expandăm datele (ZILE_SPITAL repetat de NR_PACIENTI ori)
records = [
    {"CAUZA": r.CAUZA_DOMINANTA, "ZILE_SPITAL": r.ZILE_SPITAL_MEDIE}
    for _, r in df.iterrows()
    for _ in range(int(r.NR_PACIENTI))
]
df_long = pd.DataFrame(records)

# 2) Eliminăm cauze cu n = 0
n_dict = df_long.CAUZA.value_counts()
cauze_plot = [c for c in cauze_de_afisat if n_dict.get(c, 0) > 0]
df_long = df_long[df_long.CAUZA.isin(cauze_plot)]
n_dict = n_dict.reindex(cauze_plot)

# 3) Figură
fig, ax = plt.subplots(figsize=(12, 6))

sns.boxplot(
    data=df_long, x="CAUZA", y="ZILE_SPITAL",
    order=cauze_plot,
    palette=sns.color_palette("pastel", len(cauze_plot)),
    width=0.55, linewidth=1.2, fliersize=0,   # fliersize=0 → ascunde outliers
    ax=ax
)

# 4) Mediană îngroșată
for line in ax.lines[::6]:              # fiecare box are 6 linii; prima e mediana
    line.set(linewidth=2.2, color="black")

# 5) Grilă discretă + limită 0-100
ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)
ax.set_ylim(0, 100)

# 6) Tick-uri + etichete n=...
ax.set_xticklabels(cauze_plot, rotation=30, ha="right")
for i, c in enumerate(cauze_plot):
    ax.text(i, -4, f"n = {n_dict[c]}",
            transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=9)


# 8) Titlu + label
ax.set_title("Durata spitalizării în funcție de cauza arsurii", pad=12)
ax.set_xlabel("");  ax.set_ylabel("Zile de spitalizare")
plt.subplots_adjust(bottom=0.22)        # spațiu pt etichetele n
plt.tight_layout()
plt.savefig("boxplot_durata_pe_cauza.svg")
print("✅ boxplot_durata_pe_cauza.svg salvat")



# -------- STARE EXTERNARE – afișare doar externări sub un prag --------------

prag_externari = "contact"  # tot ce vine după → doar EXTERNAT

stare = (
    df.groupby(["CAUZA_DOMINANTA", "STARE_EXTERNARE"])["NR_PACIENTI"]
      .sum().unstack(fill_value=0)
      .reindex(cauze_de_afisat, fill_value=0)
)
totals = stare.sum(axis=1)

ax = stare.plot(
    kind="bar", stacked=True, figsize=(10, 6),
    colormap="tab20", edgecolor="black", linewidth=0.4
)

for i, (idx, row) in enumerate(stare.iterrows()):
    y = 0
    doar_externat = cauze_de_afisat.index(idx) >= cauze_de_afisat.index(prag_externari)
    for col, val in row.items():
        if val:
            if doar_externat and col != "EXTERNAT":
                y += val  # nu afișa celelalte categorii
                continue
            ax.text(i, y + val / 2, str(val),
                    ha="center", va="center", fontsize=8)
            y += val

ax.set_xticklabels([f"{c}\nn={totals[c]}" for c in stare.index], rotation=30, ha="right")

ax.set_ylabel("Număr pacienți")
ax.set_xlabel("")
ax.set_title("Distribuția stării la externare în funcție de cauza arsurii", pad=12)
ax.yaxis.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

plt.tight_layout()
plt.savefig("distributie_stare_pe_cauza.svg")
print("✅ distributie_stare_pe_cauza.svg salvat (smart etichete)")


# -------- BAR Durata medie pe cauză – corect (media ponderată) --------------

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams["axes.linewidth"] = 0.8

# 1) Media ponderată pe cauză
media = (
    df.groupby("CAUZA_DOMINANTA")
      .apply(lambda g: (g.ZILE_SPITAL_MEDIE * g.NR_PACIENTI).sum() /
                       g.NR_PACIENTI.sum())
      .rename("ZILE_SPITAL_PONDERATA")
      .to_frame()
)

# 2) Număr total pacienți pe cauză
n_tot = df.groupby("CAUZA_DOMINANTA")["NR_PACIENTI"].sum()

# 3) Reindexăm în ordinea dorită
media = media.reindex(cauze_de_afisat)
n_tot = n_tot.reindex(cauze_de_afisat)

# 4) Grafic
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(
    x=media.index,
    y=media["ZILE_SPITAL_PONDERATA"],
    palette="Blues_d",
    ax=ax
)

# 5) Etichete n=... sub axă (cu offset spre dreapta)
ax.set_xticks(range(len(media.index)))
ax.set_xticklabels([""] * len(media.index))  # ascundem automatul

offset = 0.08  # deplasare spre dreapta (în unități de bară)
for i, c in enumerate(media.index):
    ax.text(
        i, -0.05,
        f"{c}\nn={n_tot[c]}",
        transform=ax.get_xaxis_transform(),
        ha="center", va="top", fontsize=9
    )

# 6) Stilizare
ax.set_ylim(0, 30)  # modifică dacă vrei altă limită superioară
ax.set_ylabel("Zile de spitalizare (medie ponderată)")
ax.set_xlabel("")
ax.set_title("Durata medie a spitalizării pe cauză de arsură", pad=12)
ax.yaxis.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

# 7) Layout & export
plt.subplots_adjust(bottom=0.28)   # spațiu pentru etichetele n
plt.tight_layout()
plt.savefig("durata_pe_cauza_corr.svg")
print("✅ durata_pe_cauza_corr.svg salvat – valori corecte & n vizibil")

