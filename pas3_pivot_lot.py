# pas3_pivot_lot.py
# Scop: genereaza pivot_arsuri_lot.xlsx
#            – media zile_spital
#            – numar pacienti unici
# Grupare: GRAD_ARSURA × CAUZA_DOMINANTA × PROCENT_INTERVAL × INTERVENTIE_CHIRURGICALA × STARE_EXTERNARE

import pandas as pd

# 1) Incarca masa master
df = pd.read_excel("master_lot.xlsx")

# 2) Verificare lot complet
assert df.precod.nunique() == 2997, "Master nu are 2997 pacienti!"

# 3) Completeaza valorile lipsa cu 'NEPRECIZAT' (pentru grupare corecta)
for col in ["GRAD_ARSURA", "CAUZA_DOMINANTA", "PROCENT_INTERVAL", "STARE_EXTERNARE"]:
    df[col] = df[col].fillna("NEPRECIZAT")

# 4) Pivot – medie zile spital (se exclude doar daca lipseste ZILE_SPITAL)
pivot_mean = pd.pivot_table(
    df,
    values="ZILE_SPITAL",
    index=[
        "GRAD_ARSURA",
        "CAUZA_DOMINANTA",
        "PROCENT_INTERVAL",
        "INTERVENTIE_CHIRURGICALA",
        "STARE_EXTERNARE",
    ],
    aggfunc="mean",
).rename(columns={"ZILE_SPITAL": "ZILE_SPITAL_MEDIE"}).round(1)

# 5) Pivot – numar pacienti unici (inclusiv cei fara ZILE_SPITAL)
pivot_n = pd.pivot_table(
    df,
    values="precod",
    index=[
        "GRAD_ARSURA",
        "CAUZA_DOMINANTA",
        "PROCENT_INTERVAL",
        "INTERVENTIE_CHIRURGICALA",
        "STARE_EXTERNARE",
    ],
    aggfunc="nunique",
).rename(columns={"precod": "NR_PACIENTI"})

# 6) Combina si reseteaza indexul
pivot = pivot_mean.join(pivot_n).reset_index()

# 7) Invariante: total pacienti
assert pivot["NR_PACIENTI"].sum() == 2997, "Suma pacientilor ≠ 2997!"

# 8) Salvare in Excel
pivot.to_excel("pivot_arsuri_lot.xlsx", index=False)
print("✅ pivot_arsuri_lot.xlsx creat (media ZILE_SPITAL + NR_PACIENTI)")
