# --------------------------------------------------------------------------
#  PREGĂTIRE DATE
# --------------------------------------------------------------------------
import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams["axes.linewidth"] = 0.8

# 1) Încarcă pivotul și filtrează cauzele dorite
df = pd.read_excel("pivot_arsuri_lot.xlsx")

cauze_de_afisat = [
    "flacara", "lichid", "contact",
    "electrica", "chimica", "solara", "explozie"
]
df = df[df["CAUZA_DOMINANTA"].isin(cauze_de_afisat)].copy()

# --------------------------------------------------------------------------
#  BOXPLOT — versiunea finală (0-60 zile, n=…, fără test statistic)
# --------------------------------------------------------------------------
# a) Expandă: câte o linie pentru fiecare pacient
records = [
    {"CAUZA": r.CAUZA_DOMINANTA, "ZILE_SPITAL": r.ZILE_SPITAL_MEDIE}
    for _, r in df.iterrows()
    for _ in range(int(r.NR_PACIENTI))
]
df_long = pd.DataFrame(records)

# b) Elimină cauzele cu n = 0
n_dict = df_long.CAUZA.value_counts()
cauze_plot = [c for c in cauze_de_afisat if n_dict.get(c, 0) > 0]
df_long = df_long[df_long.CAUZA.isin(cauze_plot)]
n_dict = n_dict.reindex(cauze_plot)

# c) Grafic
fig, ax = plt.subplots(figsize=(11, 6))
sns.boxplot(
    data=df_long, x="CAUZA", y="ZILE_SPITAL",
    order=cauze_plot,
    palette=sns.color_palette("pastel", len(cauze_plot)),
    width=0.55, linewidth=1.2, fliersize=0, ax=ax
)

# mediană îngroșată
for line in ax.lines[::6]:
    line.set(linewidth=2.2, color="black")

# axă Y 0–60 și grilă discretă
ax.set_ylim(0, 60)
ax.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)

# înlocuiește doar bucla & layout de la etichetele n=...

# ------------- ETICHETE n=... ---------------------------------------------
ax.set_xticks(range(len(cauze_plot)))
ax.set_xticklabels(cauze_plot, rotation=30, ha="right")

for i, c in enumerate(cauze_plot):
    ax.text(
        i, -0.06,                 # 6 % sub axă
        f"n = {n_dict[c]}",
        transform=ax.get_xaxis_transform(),
        ha="center", va="top", fontsize=9
    )

# ------------- LAYOUT ------------------------------------------------------
plt.subplots_adjust(bottom=0.28)   # spațiu suficient pentru n=
plt.tight_layout()
plt.savefig("boxplot_durata_pe_cauza_final.svg")
print("✅ n-urile sunt acum vizibile sub axă")

