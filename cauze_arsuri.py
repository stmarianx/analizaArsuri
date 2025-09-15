import pandas as pd
import re

# 1. Încarcă fișierul cu pacienții
df = pd.read_excel("pacienti_filtrati.xlsx")

# 2. Asigură-te că avem o coloană text pentru analiză
df['DIAGNOSTICE'] = df['DIAGNOSTICE'].fillna('').str.lower()

# 3. Definește cauzele și cuvintele cheie asociate
cauze = {
    "flacara": [
        r"\bflacara\b",
        r"fflacara",
        r"flcara",
        r"flaca",
        r"\bfalcara\b",           # typo
        r"flaara",
        r"falacara",
        r"post\s*combust",
        r"\bfoc\b",
        r"incendier[eaă]",     # incendiere / incendiera / incendieră (rar)
        r"\bbenzina\b",        # benzina nominal
        r"arsura\s+prin\s+incendiere",  # expresie completă – redundantă dar sigură
        r"fl(ac?ari|ăc?ari)"      # flacari / flăcări
    ],
    "lichid": [
        r"lichid",
        r"lichi",
        r"lichdi",
        r"linchid",
        r"lihid",
        r"fluid[e]?\s*fierbin",
        r"vapori?\s*fierbin",
        r"\babur\b",
        r"aburi?",
        r"oparir[e]?",
        r"vapori"
    ],
    "contact": [
        r"\bcontact\b",
        r"carbuni?",
        r"\bplita\b",
        r"\bgratar\b",
        r"fier\s*(incins|rosu)",
        r"incins"
    ],
    "electrocutie": [
        r"electrocut",            # corect
        r"elecrocut",             # typo lipsa t
        r"arc\s+electric",
        r"\bcurent\b",
        r"electric[ăa]?\b",            # ← prinde electric, electrica, electrică
        r"\bfulger\b",        # ← nou
        r"electricitate"
    ],
    "chimica": [
        r"chimic",
        r"\bacid\b",
        r"substanta\s+chimic",
        r"coroziv"
    ],
    "solara": [
        r"\bsolar\b",
        r"\bsolara\b",
        r"\bsoare\b",
        r"expunere\s+la\s+soare",
        r"radiat[ie]?"
    ],
    "explozie": [
        r"exploz",
        r"exploxie\b",      # typo cu x
        r"butelie",
        r"deto(n|n)are",
        r"\bincendiu\b"
    ],
}

# 4. Caută fiecare cuvânt cheie în text și creează coloane binare
for cauza, patterns in cauze.items():
    pattern_comb = '|'.join(patterns)
    df[cauza] = df['DIAGNOSTICE'].str.contains(pattern_comb, flags=re.IGNORECASE, regex=True).astype(int)

# 5. Afișează câți pacienți sunt marcați pentru fiecare cauză
print("📊 Distribuție pacienți pe cauze de arsură:\n")
for cauza in cauze.keys():
    print(f"{cauza.capitalize():<12} → {df[cauza].sum()} pacienți")

# 6. Salvează rezultatul
df_out = df[['precod', 'DIAGNOSTICE'] + list(cauze.keys())]
df_out.to_excel("cauze_arsuri.xlsx", index=False)
print("\n✅ Fișierul 'cauze_arsuri.xlsx' a fost generat.")
