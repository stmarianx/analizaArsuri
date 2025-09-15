# procente_arsura.py
"""
Extrage procentul de suprafață corporală arsă (TBSA)
din coloana DIAGNOSTICE și îl salvează în
PROCENT_SUPRAF_ARS.

 • Acceptă formele: 65%, 65 %, 65%SC, 65 :SC, 65 SC, 65: suprafața, etc.
 • Ignoră expresiile „vindecat … %” (dar nu și „în curs de vindecare”).
 • Dacă există mai multe procente:
      – Preferă PRIMUL etichetat cu „SC / suprafața …”.
      – Dacă nu există etichetă, alege MAXIMUL.
 • Dacă nu găsește procent, folosește codul T31.x (mediana intervalului).
 • Salvează:
      – pacienți_cu_procente.xlsx  (toți pacienții, cu noua coloană)
      – pacienți_exclusi_procente.xlsx  (cazurile fără procent extras)
"""

import re
import pandas as pd

# ---------------------------------------------------------
# 1. Încarc fișierul
# ---------------------------------------------------------
df = pd.read_excel("pacienti_filtrati.xlsx")

# ---------------------------------------------------------
# 2. Funcția robustă de extragere TBSA
# ---------------------------------------------------------
SC_TAG = r"(?:sc\b|suprafa[tț]a|s\.?c\.?)"        # etichete „SC”

def extrage_procent(text):
    if pd.isna(text):
        return None

    txt = str(text).replace(",", ".").lower()

    # elimină DOAR "vindecat ... %"
    txt = re.sub(
        r'vindecat[ăa]?(?: [^\d\n]{0,20})?(\d+(?:[\.,]\d+)?)\s*%',
        '',
        txt,
        flags=re.I,
    )

    # 2.1  găsește toate valorile procentuale
    pattern = rf'(~?\s*\d+(?:\.\d+)?)(?=\s*(?:%|:?{SC_TAG}))'
    procente = re.findall(pattern, txt, flags=re.I)

    if procente:
        # convertesc la float
        valori = [float(p.replace("~", "").strip()) for p in procente]

        # 2.2  prefer eticheta "SC"
        for raw in procente:
            if re.search(rf'{re.escape(raw)}\s*(?:%|:?{SC_TAG})', txt, re.I):
                return float(raw.replace("~", "").strip())

        # 2.3  altfel MAX
        return max(valori)

    # 2.4  fallback T31.x
    m = re.search(r't31\.(\d)', txt)
    if m:
        cod = int(m.group(1))
        intervale = {
            0: 5, 1: 14.5, 2: 24.5, 3: 34.5, 4: 44.5,
            5: 54.5, 6: 64.5, 7: 74.5, 8: 84.5, 9: 94.5,
        }
        return intervale.get(cod)

    return None

# ---------------------------------------------------------
# 3. Aplic funcția
# ---------------------------------------------------------
df["PROCENT_SUPRAF_ARS"] = df["DIAGNOSTICE"].apply(extrage_procent)

# --- Corecturi manuale pentru pacienți cu TBSA extras greșit ---
corectii = {
    4446124: 33.0,
    4637700: 58.0,
    4487822: 65.0,
}

df["precod"] = df["precod"].astype(int)
df.loc[df["precod"].isin(corectii.keys()), "PROCENT_SUPRAF_ARS"] = \
    df["precod"].map(corectii).combine_first(df["PROCENT_SUPRAF_ARS"])


# ---------------------------------------------------------
# 4. Salvare rezultate
# ---------------------------------------------------------
df.to_excel("pacienti_cu_procente.xlsx", index=False)
df[df["PROCENT_SUPRAF_ARS"].isna()] \
  .to_excel("pacienti_exclusi_procente.xlsx", index=False)

print("✅  Salvat 'pacienti_cu_procente.xlsx' (toți pacienții).")
print("📁  Salvat 'pacienți_exclusi_procente.xlsx' (fără procent extras).")
