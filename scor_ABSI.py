# scor_ABSI_v2.py
import re
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------
df_src = pd.read_excel("pacienti_cu_procente.xlsx")            # are PROCENT_SUPRAF_ARS
df_absi0 = pd.read_excel("baza_pacienti_ABSI.xlsx",            # ABSI vechi (doar pt. raport)
                         usecols=["precod", "ABSI_TOTAL"])

# ── coloana-cheie TBSA (procent suprafaţă arsă)
df_src["TBSA_final"] = df_src["PROCENT_SUPRAF_ARS"]

# ------------------------------------------------------------------
# 2. Importăm gradele din baza_pacienti_finala.xlsx și le îmbinăm
# ------------------------------------------------------------------
grad_cols = ["GRAD_I", "GRAD_II", "GRAD_IIA", "GRAD_IIB", "GRAD_III", "GRAD_IV"]
df_grad = pd.read_excel("baza_pacienti_finala.xlsx",
                        usecols=["precod"] + grad_cols)

df_src = df_src.merge(df_grad, on="precod", how="left")

# ──────────────────────────────────────────────────────────────
# 2.b  Importăm flag-ul IS_SECHELE din baza_pacienti_ABSI.xlsx

df_sech = pd.read_excel("baza_pacienti_ABSI.xlsx",
                         usecols=["precod", "IS_SECHELE"])
df_src  = df_src.merge(df_sech, on="precod", how="left")


df_src["IS_SECHELE"] = df_src["IS_SECHELE"].fillna(0).astype(int)

# listez gradele de la cel mai sever la cel mai uşor
grad_priority = [
    ("GRAD_IV",  4),
    ("GRAD_III", 3),
    ("GRAD_IIB", 2),
    ("GRAD_IIA", 2),
    ("GRAD_II",  2),
    ("GRAD_I",   1),
]

def pick_grad_max(row):
    for col, num in grad_priority:
        if col in row and pd.notna(row[col]) and row[col] > 0:
            return num
    return np.nan

df_src["Grad_max"] = df_src.apply(pick_grad_max, axis=1).astype("Int64")

# ------------------------------------------------------------------
# 3. Extragem leziuni inhalatorii / circumferenţiale / data arsurii
# Helper-uri (în scor_ABSI_v2.py și în orice alt script de pre-parsing)
inh_pat = re.compile(
    r"(?:"
    r"\btrs\b"                            # TRS
    r"|inhal\w*"                          # inhalare, inhalatorii…
    r"|fum[-_/ ]*inhal\w*"                # fum inhalat…
    r"|injhal\w*"                         # injhal…
    r"|(?:căi|cai)\s+(?:aeriene|resp\w*)" # căi aeriene / respiratorii
    r"|tract[-_/ ]*resp\w*"               # tract respirator
    r"|insuficien[țt]a\s+respiratorie"    # insuficienţă respiratorie
    r"|cas\b"                       # abreviere locală pentru airway burn
    r")",
    re.I
)

circ_pat = re.compile(r"circumferen[țt]ial", re.I)
date_pat = re.compile(r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})")
absi_pat = re.compile(
    r"\bABSI\s*[:=\-]?\s*(\d{1,2})(?!\d)",  # look-ahead: după cifre nu mai vine altă cifră
    re.I
)

# ──────────────────────────────────────────────────────────────
# 2.c  Corectăm pacienții marcați greșit ca sechele
#      ⇒ „șoc postcombustional” dar fără termeni de sechele
# ──────────────────────────────────────────────────────────────
REG_SECHELE      = re.compile(r"(sechel|cicatric|brida|alopecie\\s+postcomb|contractur)",
                              re.I)
REG_SOC_POSTCOMB = re.compile(r"(?:s|ș)oc\s+postcomb", re.I)

txt_series   = df_src["DIAGNOSTICE"].fillna("")
mask_wrong   = (
    (df_src["IS_SECHELE"] == 1)
    & txt_series.str.contains(REG_SOC_POSTCOMB)
    & ~txt_series.str.contains(REG_SECHELE)
)
n_wrong = int(mask_wrong.sum())
if n_wrong:
    logging.info("Corectez IS_SECHELE → 0 pentru %d pacienți cu șoc postcombustional",
                 n_wrong)
    df_src.loc[mask_wrong, "IS_SECHELE"] = 0
print(f"✔  IS_SECHELE schimbat la {n_wrong} pacienți (soc postcombustional fără sechele)")



def parse_row(txt: str):
    if pd.isna(txt):
        return pd.Series([0, 0, pd.NaT, np.nan])

    inh  = int(bool(inh_pat.search(txt)))
    circ = int(bool(circ_pat.search(txt)))

    # data arsurii
    burn_date = pd.NaT
    for dstr in date_pat.findall(txt):
        try:
            burn_date = pd.to_datetime(dstr, dayfirst=True, errors="raise")
            break
        except Exception:
            continue

    # ABSI consemnat manual (dacă există)
    m = absi_pat.search(txt)
    absi_txt = float(m.group(1)) if m else np.nan

    return pd.Series([inh, circ, burn_date, absi_txt])


df_src[["LeziuniInhalatorii", "LeziuniCircumf",
        "Data_Ars", "ABSI_text"]] = df_src["DIAGNOSTICE"].apply(parse_row)


# ------------------------------------------------------------------
# 4. Timp ars–internare
# ------------------------------------------------------------------
df_src["DATA_INTERNARE"] = pd.to_datetime(df_src["DATA_INTERNARE"], errors="coerce")
df_src["Timp_Ars_Internare_zile"] = (
    df_src["DATA_INTERNARE"] - pd.to_datetime(df_src["Data_Ars"], errors="coerce")
).dt.days

# ------------------------------------------------------------------
# 5. Componente ABSI
# ------------------------------------------------------------------
def age_pts(a):              # punctaj vârstă
    return pd.cut([a], [0,20,40,60,80,120], labels=[1,2,3,4,5])[0]

def tbsa_pts(p):
    if pd.isna(p):
        return np.nan
    #  intervalele 1-10, 11-20, 21-30 … 91-100
    bins   = [0,10,20,30,40,50,60,70,80,90,100]
    labels = range(1,11)                 # 1-10 puncte
    return pd.cut([p], bins=bins, labels=labels, right=True, include_lowest=True)[0]


df_src["ABSI_SEX"] = (df_src["SEX"].str.upper() == "F").astype(int)
df_src["ABSI_AGE"]        = df_src["VARSTA"].apply(age_pts).astype(float)
df_src["ABSI_INHAL"]      = df_src["LeziuniInhalatorii"]
df_src["ABSI_FULL_THICK"] = (
    df_src["Grad_max"].fillna(0) >= 3      # <NA> → 0
).astype(int)

df_src["ABSI_BSA"]        = df_src["TBSA_final"].apply(tbsa_pts).astype(float)

absi_cols = ["ABSI_SEX", "ABSI_AGE", "ABSI_INHAL",
             "ABSI_FULL_THICK", "ABSI_BSA"]
df_src["ABSI_TOTAL"] = df_src[absi_cols].sum(axis=1, min_count=5)

df_src["delta_ABSI_text"] = (
    df_src["ABSI_TOTAL"] - df_src["ABSI_text"]
)

# ------------------------------------------------------------------
# 6.b  Predicția ABSI – o singură coloană text (ABSI_PRED)
# ------------------------------------------------------------------
def absi_pred(total: float) -> str:
    if pd.isna(total):
        return "NA"
    t = int(total)
    if   t <= 3:   return "Very low (≥ 99 %)"
    elif t <= 5:   return "Moderate (98 %)"
    elif t <= 7:   return "Moderately severe (80-90 %)"
    elif t <= 9:   return "Serious (50-70 %)"
    elif t <= 11:  return "Severe (20-40 %)"
    else:          return "Maximum (≤ 10 %)"

df_src["ABSI_PRED"] = df_src["ABSI_TOTAL"].apply(absi_pred)



# marcăm discrepanțe semnificative (>1 punct)
df_src["Flag_ABSI_mismatch"] = (
    df_src["delta_ABSI_text"].abs() > 1
).fillna(False)

df_src.loc[df_src["Flag_ABSI_mismatch"],
           ["precod", "ABSI_text", "ABSI_TOTAL", "delta_ABSI_text",
            "DIAGNOSTICE"]] \
      .to_csv("audit_ABSI_text_mismatch.csv", index=False)


# ------------------------------------------------------------------
# 6. Raport diferenţe vs. scorul vechi
# ------------------------------------------------------------------
df_new_vs_old = df_src[["precod", "ABSI_TOTAL"]] \
    .merge(df_absi0, on="precod", how="left",
           suffixes=("_new", "_old"))
df_new_vs_old["delta"] = df_new_vs_old["ABSI_TOTAL_new"] - df_new_vs_old["ABSI_TOTAL_old"]
df_new_vs_old.loc[df_new_vs_old["delta"].abs() != 0] \
              .to_csv("raport_dif_ABSI.csv", index=False)

# ------------------------------------------------------------------
# 7. Fuziune cu baza veche și actualizare coloane
# ------------------------------------------------------------------
df_orig   = pd.read_excel("baza_pacienti_ABSI.xlsx")
orig_cols = df_orig.columns.tolist()

# ► înlocuiește definiția lui df_new cu varianta de mai jos  ◄
df_new = df_src[[
    "precod",
    # scor ABSI – componente
    "ABSI_SEX", "ABSI_AGE", "ABSI_INHAL",
    "ABSI_FULL_THICK", "ABSI_BSA",
    # scor total
    "ABSI_TOTAL",
    "ABSI_PRED",
    # restul variabilelor pe care vrei să le cobori
    "IS_SECHELE",
    "TBSA_final", "Grad_max",
    "LeziuniInhalatorii", "LeziuniCircumf",
    "Data_Ars", "Timp_Ars_Internare_zile",
]].rename(columns={"ABSI_TOTAL": "ABSI_TOTAL_new"})


df_final = df_orig.merge(df_new, on="precod", how="left",
                         suffixes=("_old", "_new"))

# – păstrez valorile noi pentru câmpuri potenţial duplicate
for col in ["Grad_max","LeziuniInhalatorii",
            "LeziuniCircumf","ABSI_FULL_THICK"]:
    if f"{col}_new" in df_final.columns:
        df_final.drop(columns=[f"{col}_old"], errors="ignore", inplace=True)
        df_final.rename(columns={f"{col}_new": col}, inplace=True)

for col in [
    "ABSI_SEX", "ABSI_AGE", "ABSI_INHAL", "ABSI_PRED",
    "ABSI_FULL_THICK", "ABSI_BSA", "IS_SECHELE"
]:
    if f"{col}_new" in df_final.columns:
        df_final.drop(columns=[f"{col}_old"], errors="ignore", inplace=True)
        df_final.rename(columns={f"{col}_new": col}, inplace=True)



# – înlocuiesc scorul, calculez delta_ABSI
df_final["delta_ABSI"] = df_final["ABSI_TOTAL_new"] - df_final["ABSI_TOTAL"]
df_final.drop(columns=["ABSI_TOTAL"], inplace=True)
df_final.rename(columns={"ABSI_TOTAL_new": "ABSI_TOTAL"}, inplace=True)

# – rearanjez coloanele: iniţiale + cele noi
if "ABSI_TOTAL" in orig_cols:
    orig_cols.remove("ABSI_TOTAL")
ordered_cols = orig_cols + [c for c in df_final.columns if c not in orig_cols]
df_final = df_final[ordered_cols]

# ------------------------------------------------------------------
# ------------------------------------------------------------------
# 8. Export – două foi: pacienți + codebook
# ------------------------------------------------------------------
out_file = "baza_pacienti_ABSI_v2.xlsx"

with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
    # foaia principală cu datele complete
    df_final.to_excel(writer, sheet_name="pacienti", index=False)

    # codebook – un singur vector cu numele coloanelor
    pd.DataFrame({"column": df_final.columns}) \
      .to_excel(writer, sheet_name="codebook", index=False)

print(f"✔  {out_file} creat – foi: pacienți & codebook")

