import pandas as pd
import re

# 1. Încarcă fișierul
df_analize = pd.read_excel("analize_filtrate.xlsx")

# 2. Extrage denumirile unice
denumiri_brute = df_analize['ANANUME'].dropna().unique()

# 3. Normalizează denumirile
def normalize(den):
    den = den.lower()
    den = re.sub(r'[\*\(\)\[\]\{\}\-]', '', den)     # elimină simboluri speciale
    den = re.sub(r'\s+', '_', den)                   # spații → _
    den = re.sub(r'[^a-z0-9_]', '', den)             # doar litere/cifre/_
    return den.strip('_')

denumiri_normalizate = [normalize(d) for d in denumiri_brute]
distincte = sorted(set(denumiri_normalizate))

# 4. Creează tabel de verificare
df_out = pd.DataFrame({
    'ANANUME_ORIGINAL': denumiri_brute,
    'ANANUME_NORMALIZAT': denumiri_normalizate
}).sort_values(by='ANANUME_NORMALIZAT')

# 5. Afișează numărul total
print(f"✅ Sunt {len(distincte)} analize distincte după normalizare.")

# 6. Salvează lista
df_out.to_excel("analize_distincte.xlsx", index=False)
