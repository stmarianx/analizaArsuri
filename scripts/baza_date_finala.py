import pandas as pd
import re
import time

t_total = time.time()

print("📥 1. Încarc fișierele...")
t1 = time.time()
df_analize = pd.read_excel("analize_pe_zi.xlsx")
df_pacienti = pd.read_excel("pacienti_filtrati.xlsx")
print(f"✔️ Încărcat în {round(time.time() - t1, 2)} sec.\n")

# -----------------------------------------
print("🔧 2. Codific variabilele demografice...")
t2 = time.time()
df_pacienti['SEX'] = df_pacienti['SEX'].map({'F': 0, 'M': 1})
df_pacienti['MEDIU'] = df_pacienti['MEDIU'].map({'u': 0, 'r': 1})
df_pacienti['STATUS'] = df_pacienti['TIP_EXTERNARE'].str.upper().apply(lambda x: 1 if 'DECEDAT' in x else 0)
df_pacienti['TRATAMENT'] = df_pacienti['INTERVENTIE_CHIRURGICALA'].notna().astype(int)
print(f"✔️ Codificare demografică în {round(time.time() - t2, 2)} sec.\n")

# -----------------------------------------
print("📦 3. One-hot encoding pentru DIAG_PRINCIPAL...")
t3 = time.time()
df_diag_principal = pd.get_dummies(df_pacienti['DIAG_PRINCIPAL'].fillna(''), prefix='DP', prefix_sep='_')
df_diag_principal_grp = df_pacienti[['precod']].join(df_diag_principal).groupby('precod').max()
df_diag_principal_grp = df_diag_principal_grp.astype(int)
print(f"✔️ {df_diag_principal.shape[1]} coduri principale în {round(time.time() - t3, 2)} sec.\n")

# -----------------------------------------
print("📦 4. One-hot encoding pentru DIAG_SECUNDARE (coduri ICD)...")
t4 = time.time()

def extrage_coduri_icd(text):
    if pd.isna(text): return []
    return re.findall(r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b', text.upper())

diag_sec_set = set()
diag_sec_per_pacient = []

for text in df_pacienti['DIAG_SECUNDARE']:
    coduri = extrage_coduri_icd(text)
    diag_sec_set.update(coduri)
    diag_sec_per_pacient.append(coduri)

diag_sec_list = sorted(list(diag_sec_set))
df_diag_secundar = pd.DataFrame(0, index=df_pacienti.index, columns=[f'DS_{c}' for c in diag_sec_list])

for i, coduri in enumerate(diag_sec_per_pacient):
    for cod in coduri:
        col = f'DS_{cod}'
        if col in df_diag_secundar.columns:
            df_diag_secundar.at[i, col] = 1

df_diag_secundar_grp = df_pacienti[['precod']].join(df_diag_secundar).groupby('precod').max()
df_diag_secundar_grp = df_diag_secundar_grp.astype(int)
print(f"✔️ {len(diag_sec_list)} coduri secundare în {round(time.time() - t4, 2)} sec.\n")


# -----------------------------------------
print("🔗 5. Pregătesc metadatele pentru merge...")
t5 = time.time()
df_meta = df_pacienti[['precod', 'VARSTA', 'SEX', 'MEDIU', 'STATUS', 'TRATAMENT']].drop_duplicates(subset='precod')
print(f"✔️ Metadate pregătite în {round(time.time() - t5, 2)} sec.\n")

# -----------------------------------------
print("🔗 6. Combin toate componentele într-un singur tabel...")
t6 = time.time()
df_final = df_analize.merge(df_meta, on='precod', how='left')
df_final = df_final.merge(df_diag_principal_grp, on='precod', how='left')
df_final = df_final.merge(df_diag_secundar_grp, on='precod', how='left')
print(f"✔️ Tabel final: {df_final.shape[0]} rânduri, {df_final.shape[1]} coloane în {round(time.time() - t6, 2)} sec.\n")

# -----------------------------------------
print("💾 7. Salvez fișierul final...")
t7 = time.time()
df_final.to_excel("baza_date_completa.xlsx", index=False)
print(f"✔️ Fișier salvat în {round(time.time() - t7, 2)} sec.")

print(f"\n✅ Script finalizat în {round(time.time() - t_total, 2)} secunde.")
