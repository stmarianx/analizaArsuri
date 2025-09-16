# pas2_prepare_master.py
# Creează master_lot.xlsx (un rând = 1 pacient din lotul de 2 997)

import pandas as pd
import re
from datetime import datetime

# 1. Citim baza principală (aceasta conţine DIAG_* şi DIAGNOSTICE)
# ------------------------------------------------------------
df = pd.read_excel("pacienti_cu_procente.xlsx")

# Dacă vrei să adaugi coloane din cauze_arsuri.xlsx:
try:
    df_cauze = pd.read_excel("cauze_arsuri.xlsx")
    df = df.merge(df_cauze.drop(columns=["DIAGNOSTICE",
                                         "DIAG_PRINCIPAL",
                                         "DIAG_SECUNDARE"],
                                errors="ignore"),
                  on="precod", how="left")
except FileNotFoundError:
    print("⚠️  cauze_arsuri.xlsx nu găsit – continui fără coloanele de cauză")

# ------------------------------------------------------------------
# 3. Coloane derivate (cauză dominantă, interval TBSA, zile spital etc.)
# ------------------------------------------------------------------
CAUSES = ["flacara", "lichid", "contact", "electrocutie",
          "chimica", "solara", "explozie"]

df["CAUZA_DOMINANTA"] = df[CAUSES].idxmax(axis=1)
df.loc[df[CAUSES].sum(axis=1) == 0, "CAUZA_DOMINANTA"] = "NEPRECIZAT"

bins   = [0, 10, 30, 50, 70, 90, 100]
labels = ["0–10%", "11–30%", "31–50%", "51–70%", "71–90%", "91–100%"]
df["PROCENT_INTERVAL"] = pd.cut(
    df["PROCENT_SUPRAF_ARS"], bins=bins, labels=labels,
    include_lowest=True
).astype(str).fillna("NEPRECIZAT")

df["DATA_INTERNARE"] = pd.to_datetime(df["DATA_INTERNARE"], errors="coerce")
df["DATA_EXTERNARE"] = pd.to_datetime(df["DATA_EXTERNARE"], errors="coerce")
df["ZILE_SPITAL"]    = (df["DATA_EXTERNARE"] - df["DATA_INTERNARE"]).dt.days

df["INTERVENTIE_CHIRURGICALA"] = (
    df["INTERVENTIE_CHIRURGICALA"].fillna("").astype(str).str.strip().ne("").astype(int)
)

df["STARE_EXTERNARE"] = df["TIP_EXTERNARE"].fillna("Necunoscut").str.upper()

# ------------------------------------------------------------------
# 4. Text concatenat pentru NLP / regex
# ------------------------------------------------------------------
df["TEXT_ANALIZAT"] = (
    df["DIAGNOSTICE"].fillna("").str.lower() + " " +
    df["EPICRIZA"].fillna("").str.lower()
)

# ------------------------------------------------------------------
# 5. Detectare GRAD (I … IV)
# ------------------------------------------------------------------
pat_grad = {
    "I": [
        r"\bgrad(?:ul)?[\s.\-]*i\b(?![iv])",
        r"\bgr[\s.\-]*1\b",
        r"\bgr\s*i\b(?![iv])",
        r"(?:grad|gr)[\s.\-]*i(?![iv])|\b(?:grad|gr)[\s.\-]*1\b",
        r"\bgard(?:ul)?[\s.\-]*i\b(?![iv])",
        r"\bgrd[\s.\-]*i\b",
        r"\bgradv[\s.\-]*i\b",
    ],

    "II": [
        # II singur (roman) – fara 'iii', 'iia', 'iib'
        r"\bgrad(?:ul)?[\s.\-]*(?<!i)ii\b(?!i)(?![ab])",
        r"\bgrad(?:ul)?[\s.\-]*2\b(?![ab])",

        # abrevieri
        r"\bgr[\s.\-]*(?<!i)ii\b(?!i)(?![ab])",
        r"\bgrd[\s.\-]*(?<!i)ii\b(?!i)",
        r"\bgd[\s.\-]*(?<!i)ii\b(?!i)(?![ab])",
        r"\bgard(?:ul)?[\s.\-]*(?<!i)ii\b(?!i)(?![ab])",
        r"\bgr[\s.\-]*2\b(?![ab])",
        r"\bgrd[\s.\-]*2\b(?![ab])",

        # I–II cu orice separator si spatii
        r"\bgrad\s*i\s*[-–/\\]\s*ii\b",
        r"\bgr\s*i\s*[-–/\\]\s*ii\b",
        r"\bgradul\s*i\s*[-–]?ii\b",
        r"\bgr\s*i\s*[-–]?ii\b",
    ],

    "IIA": [
        r"\bgrad(?:ul)?[\s.\-]*ii[\s.\-]*a\b",
        r"\bgr[\s.\-]*2[\s.\-]*a\b",
        r"\bgr[\s.\-]*iia\b",
        r"(?:grad|gr)[\s.\-]*ii[\s.\-]*a|\b(?:grad|gr)[\s.\-]*2[\s.\-]*a\b",
        r"\bgard(?:ul)?[\s.\-]*ii[\s.\-]*a\b",
        r"\bgrd[\s.\-]*2[\s.\-]*a\b",
        r"\bgrad(?:ul)?[\s.\-]*2[\s.\-]*a[/\\-]*b?\b",
    ],

    "IIB": [
        r"\bgrad(?:ul)?[\s.\-]*ii[\s.\-]*b\b",
        r"\bgr[\s.\-]*2[\s.\-]*b\b",
        r"\bgr[\s.\-]*iib\b",
        r"(?:grad|gr)[\s.\-]*ii[\s.\-]*b|\b(?:grad|gr)[\s.\-]*2[\s.\-]*b\b",
        r"\bgard(?:ul)?[\s.\-]*ii[\s.\-]*b\b",
        r"\bgrd[\s.\-]*2[\s.\-]*b\b",
        r"\bgrad(?:ul)?[\s.\-]*2[\s.\-]*b[/\\-]*a?\b",
    ],

    "III": [
        # forme simple
        r"\bgrad(?:ul)?[\s.\-]*iii\b",
        r"\bgr[\s.\-]*3\b(?!\d)",
        r"\bgradul\s*iii\b",
        r"\bgradul\s*3\b(?!\d)",
        r"(?:grad|gr)[\s.\-]*iii|\b(?:grad|gr)[\s.\-]*3\b",
        r"\bgard(?:ul)?[\s.\-]*iii\b",
        r"\bgradv[\s.\-]*iii\b",
        r"\bgrd[\s.\-]*iii\b",
        r"\bgrd[\s.\-]*3\b",
        r"\bgd[\s.\-]*iii\b",
        r"\bgraf[\s.\-]*iii\b",

        # II–III cu separatori si spatii
        r"\bgrad[\s.\-]*ii\s*[-–/\\]\s*iii\b",
        r"\bgrd[\s.\-]*ii\s*[-–/\\]\s*iii\b",
        r"\bgr[\s.\-]*ii\s*[-–/\\]\s*iii\b",
        r"\bii\s*[-–/\\]\s*iii\b",
        r"\bgrd[\s.\-]*ii[-/\\]*iii\b",
        r"\bgrad(?:ul)?[\s.\-]*2\s*[-–/\\]\s*3\b",
        r"\bgrad(?:ul)?[\s.\-]*2[\s.\-]*3\b",

        # IIA / IIB – III
        r"\biia\s*[-–/\\]\s*iii\b",
        r"\biib\s*[-–/\\]\s*iii\b",

        # I–II–III
        r"\bgrad\s*i\s*[-–/\\]\s*ii\s*[-–/\\]\s*iii\b",
        r"\bgr\s*i\s*[-–/\\]\s*ii\s*[-–/\\]\s*iii\b",

        r"\bii\s*[ab]?\s*[-–/\\]\s*iii\b",          # II, IIA/IIB – III
        r"\bgrad\s*ii\s*[ab]?\s*[-–/\\]\s*iii\b",
        r"\bgrd?\s*ii\s*[ab]?\s*[-–/\\]\s*iii\b",


        # III–IV si 3–4 (seteaza si III)
        r"\bgrad(?:ul)?[\s.\-]*iii\s*[-–/\\]\s*iv\b",
        r"\bgr[\s.\-]*iii\s*[-–/\\]\s*iv\b",
        r"\bgrad(?:ul)?[\s.\-]*3\s*[-–/\\]\s*4\b",
        r"\bgr[\s.\-]*3\s*[-–/\\]\s*4\b",
        r"\bgrad(?:ul)?[\s.\-]*iii[\s.\-/]*iv\b",
        r"\bgrad(?:ul)?[\s.\-]*3[\s.\-/]*4\b",
        r"\bgr[\s.\-]*iii[\s.\-/]*iv\b",
        r"\bgr[\s.\-]*3[\s.\-/]*4\b",
    ],

    "IV": [
        r"\bgrad(?:ul)?[\s.\-]*iv\b",
        r"\bgr(?:ad)?[\s.\-]*4\b",
        r"\bgr[\s.\-]*iv\b",
        r"(?:grad|gr)[\s.\-]*iv|\b(?:grad|gr)[\s.\-]*4\b",
        r"\bgard(?:ul)?[\s.\-]*iv\b",
        r"\bgradv[\s.\-]*iv\b",
        r"\bgrd[\s.\-]*4\b",
        r"\bgd[\s.\-]*iv\b",
        r"\bgraf[\s.\-]*iv\b",

        # III–IV / 3–4 (seteaza si IV)
        r"\bgrad(?:ul)?[\s.\-]*iii\s*[-–/\\]\s*iv\b",
        r"\bgr[\s.\-]*iii\s*[-–/\\]\s*iv\b",
        r"\bgrad(?:ul)?[\s.\-]*3\s*[-–/\\]\s*4\b",
        r"\bgr[\s.\-]*3\s*[-–/\\]\s*4\b",
        r"\bgrad(?:ul)?[\s.\-]*iii[\s.\-/]*iv\b",
        r"\bgrad(?:ul)?[\s.\-]*3[\s.\-/]*4\b",
        r"\bgr[\s.\-]*iii[\s.\-/]*iv\b",
        r"\bgr[\s.\-]*3[\s.\-/]*4\b",
    ],
}


# iniţializează coloane binare
for g in pat_grad.keys():
    df[f"GRAD_{g}"] = 0

# marchează 1 când se potriveşte oricare dintre pattern-uri
for g, patterns in pat_grad.items():
    regex = r"(" + r"|".join(patterns) + r")"
    mask  = df["TEXT_ANALIZAT"].str.contains(regex, regex=True, na=False, case=False)
    df.loc[mask, f"GRAD_{g}"] = 1

# ------------------------------------------------------------------
# 6. Fallback pentru grosime completă (full-thickness)
# ------------------------------------------------------------------
ICD_FULL = re.compile(r"\bT\d{2}\.(?:\d)?[34]\b", re.I)       # T**.3 / T**.4

mask_icd = (
    df["DIAG_PRINCIPAL"].fillna("").str.contains(ICD_FULL) |
    df["DIAG_SECUNDARE"].fillna("").str.contains(ICD_FULL)
)

df.loc[mask_icd, "GRAD_III"] = 1        # nu deranjăm GRAD_IV

# ------------------------------------------------------------------
# 7. Coloana sumar GRAD_ARSURA
# ------------------------------------------------------------------
grad_order = ["IV", "III", "IIB", "IIA", "II", "I"]   # sever → uşor

def grad_max(row) -> str:
    for g in grad_order:
        if row[f"GRAD_{g}"] == 1:
            return g
    return "NEPRECIZAT"

df["GRAD_ARSURA"] = df.apply(grad_max, axis=1)

# ------------------------------------------------------------------
# 8. Export
# ------------------------------------------------------------------
print("\n📊 Distribuţie GRAD_* (sumă de 1-uri pe coloană):")
print(df[[f"GRAD_{g}" for g in pat_grad]].sum())

df.to_excel("master_lot.xlsx", index=False)
print("✅  master_lot.xlsx creat / actualizat —", datetime.now().strftime("%Y-%m-%d %H:%M"))
