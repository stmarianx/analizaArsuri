import pandas as pd
import time
import re

start_total = time.time()

print("1. Încarc fișierele...")
df_pacienti = pd.read_excel("pacienti_filtrati.xlsx")
df_analize = pd.read_excel("analize_filtrate.xlsx")

# ============================
# 2. Codificare demografică
# ============================
print("2. Codific variabilele demografice...")
df_pacienti['SEX'] = df_pacienti['SEX'].map({'F': 0, 'M': 1})
df_pacienti['MEDIU'] = df_pacienti['MEDIU'].map({'u': 0, 'r': 1})
df_pacienti['STATUS'] = df_pacienti['TIP_EXTERNARE'].str.upper().apply(lambda x: 1 if 'DECEDAT' in x else 0)
df_pacienti['TRATAMENT'] = df_pacienti['INTERVENTIE_CHIRURGICALA'].notna().astype(int)

# ============================
# 3. One-hot encoding diag. principal
# ============================
print("3. Codific diag. principal (one-hot)...")
diag_principal_dummies = pd.get_dummies(df_pacienti['DIAG_PRINCIPAL'].fillna(''), prefix='DP', prefix_sep='_')

# ============================
# 4. Filtrare și codificare diag. secundar (valid ICD)
# ============================
print("4. Extrag coduri valide din diag. secundar...")

def extrage_coduri_icd(text):
    if pd.isna(text): return []
    return re.findall(r'[A-Z]\d{2}(?:\.\d)?', text.upper())

diag_sec_list = set()
diag_sec_per_pacient = []

for text in df_pacienti['DIAG_SECUNDARE']:
    coduri = extrage_coduri_icd(text)
    diag_sec_list.update(coduri)
    diag_sec_per_pacient.append(coduri)

diag_sec_list = sorted(diag_sec_list)
diag_sec_dummies = pd.DataFrame(0, index=df_pacienti.index, columns=[f'DS_{c.replace(".", "_")}' for c in diag_sec_list])

for i, coduri in enumerate(diag_sec_per_pacient):
    for cod in coduri:
        col = f'DS_{cod.replace(".", "_")}'
        diag_sec_dummies.at[i, col] = 1

# ============================
# 5. Pivotare analize
# ============================
print("5. Pivot analize per zi per pacient...")
df_analize['setdata'] = pd.to_datetime(df_analize['setdata']).dt.date
df_analize_pivot = df_analize.pivot_table(
    index=['precod', 'setdata'],
    columns='ANANUME',
    values='valoare_numerica',
    aggfunc='first'
)

df_analize_pivot.columns = ['AN_' + str(col).strip().replace(' ', '_') for col in df_analize_pivot.columns]
df_analize_pivot = df_analize_pivot.reset_index()

# ============================
# 6. Combinare finală
# ============================
print("6. Combin datele într-un singur tabel...")
df_meta = df_pacienti[['precod', 'VARSTA', 'SEX', 'MEDIU', 'STATUS', 'TRATAMENT']].copy()
df_final = df_analize_pivot.merge(df_meta, on='precod', how='left')
df_final = df_final.merge(diag_principal_dummies, left_on='precod', right_index=True, how='left')
df_final = df_final.merge(diag_sec_dummies, left_on='precod', right_index=True, how='left')

# ============================
# 7. Salvare
# ============================
print("7. Salvez fișierul final: baza_date_numerica_v2.xlsx...")
df_final.to_excel("baza_date_numerica.xlsx", index=False)

print(f"\n✅ Finalizat în {round(time.time() - start_total, 2)} secunde.")
