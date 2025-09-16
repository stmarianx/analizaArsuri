import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Citim fișierul filtrat
df = pd.read_excel("pacienti_filtrati.xlsx")

# ✅ 1. Distribuția pe sex
distributie_sex = df['SEX'].value_counts()
print("\nDistribuție pe sex:")
print(distributie_sex)

distributie_sex.plot(kind='bar', title='Distribuție pe sex')
plt.xlabel("Sex")
plt.ylabel("Număr pacienți")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("distributie_sex.png")
plt.clf()

# ✅ 2. Distribuția pe grupe de vârstă
bins = [0, 20, 40, 60, 100]
labels = ['0–20', '21–40', '41–60', '60+']
df['grupa_varsta'] = pd.cut(df['VARSTA'], bins=bins, labels=labels, right=False)

grupe_varsta = df['grupa_varsta'].value_counts().sort_index()
print("\nDistribuție pe grupe de vârstă:")
print(grupe_varsta)

grupe_varsta.plot(kind='bar', title='Distribuție pe grupe de vârstă')
plt.xlabel("Grupă de vârstă")
plt.ylabel("Număr pacienți")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("distributie_varsta.png")
plt.clf()

# ✅ 3. Distribuția pe mediu (dacă există coloana)
if 'MEDIU' in df.columns:
    distributie_mediu = df['MEDIU'].value_counts()
    print("\nDistribuție pe mediu:")
    print(distributie_mediu)

    distributie_mediu.plot(kind='bar', title='Distribuție pe mediu de proveniență')
    plt.xlabel("Mediu")
    plt.ylabel("Număr pacienți")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("distributie_mediu.png")
    plt.clf()

# ✅ 4. Durata spitalizării – dacă avem coloanele necesare
if 'DATA_INTERNARE' in df.columns and 'DATA_EXTERNARE' in df.columns:
    df['DATA_INTERNARE'] = pd.to_datetime(df['DATA_INTERNARE'])
    df['DATA_EXTERNARE'] = pd.to_datetime(df['DATA_EXTERNARE'])
    df['ZILE_SPITAL'] = (df['DATA_EXTERNARE'] - df['DATA_INTERNARE']).dt.days

    print("\nStatistici durată internare (în zile):")
    print(df['ZILE_SPITAL'].describe())

    df['ZILE_SPITAL'].hist(bins=30)
    plt.title("Histogramă durată spitalizare")
    plt.xlabel("Zile")
    plt.ylabel("Număr pacienți")
    plt.tight_layout()
    plt.savefig("durata_spitalizare.png")
    plt.clf()

# Clasificăm pacienții în Decedat / Externat pe baza TIP_EXTERNARE
df['STATUS'] = df['TIP_EXTERNARE'].str.upper().apply(
    lambda x: 'Decedat' if 'DECEDAT' in x else 'Externat'
)

# Distribuție pe status
distributie_status = df['STATUS'].value_counts()
print("\nDistribuție pacienți la externare (după TIP_EXTERNARE):")
print(distributie_status)

# Grafic
distributie_status.plot(kind='bar', title='Distribuție pacienți la externare', color=['green', 'red'])
plt.xlabel("Status la externare")
plt.ylabel("Număr pacienți")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("distributie_status.png")
plt.clf()

# Etapa 3: Comparatie decedat vs externat
# -------------------------------

# [grafic status externare]
# [boxplot varsta vs status]
# [boxplot durata spitalizare vs status]


# Asigurăm că coloana ZILE_SPITAL există
df['DATA_INTERNARE'] = pd.to_datetime(df['DATA_INTERNARE'])
df['DATA_EXTERNARE'] = pd.to_datetime(df['DATA_EXTERNARE'])
df['ZILE_SPITAL'] = (df['DATA_EXTERNARE'] - df['DATA_INTERNARE']).dt.days

# ✅ Boxplot: Vârstă vs. Status
sns.boxplot(data=df, x='STATUS', y='VARSTA', order=['Externat', 'Decedat'], palette=['green', 'red'])
plt.title("Distribuția vârstei: Externat vs. Decedat")
plt.xlabel("Status")
plt.ylabel("Vârstă (ani)")
plt.tight_layout()
plt.savefig("varsta_vs_status.png")
plt.clf()

# Filtreaza doar pacientii cu durata <= 60 zile
df_limitat = df[df['ZILE_SPITAL'] <= 60]

sns.boxplot(
    data=df_limitat,
    x='STATUS',
    y='ZILE_SPITAL',
    order=['Externat', 'Decedat'],
    palette=['green', 'red'],
    showfliers=False  # 🔴 elimină cerculețele
)

plt.title("Durata spitalizării : Externat vs. Decedat")
plt.xlabel("Status")
plt.ylabel("Zile de spitalizare")
plt.tight_layout()
plt.savefig("spital_vs_status.png")
plt.clf()


# 1. Ai putea face grafice mai complexe, cum ar fi de ex distribuția pe sexe și pe ani? Și să treci nr pacienților pe fiecare plot din grafic?


# Grupăm pe ani și sex și numărăm pacienții
grupare = df.groupby(['an', 'SEX']).size().reset_index(name='NR_PACIENTI')

# Sortăm pentru un grafic clar
grupare = grupare.sort_values(['an', 'SEX'])

# Stil și dimensiuni
plt.figure(figsize=(12, 6))
ax = sns.barplot(data=grupare, x='an', y='NR_PACIENTI', hue='SEX', palette=['#4CAF50', '#2196F3'])

# Adăugăm numărul pacienților deasupra fiecărei bare
for container in ax.containers:
    ax.bar_label(container, fmt='%d', label_type='edge', padding=3)

plt.title("Distribuția pacienților pe ani și sex")
plt.xlabel("An")
plt.ylabel("Număr pacienți")
plt.legend(title="Sex", loc='upper right')
plt.tight_layout()
plt.savefig("distributie_ani_sex.png")


# Definim grupele de varsta
bins = [0, 20, 40, 60, 120]
labels = ['0–20', '21–40', '41–60', '60+']
df['grupa_varsta'] = pd.cut(df['VARSTA'], bins=bins, labels=labels, right=False)

# Grupăm după an și grupă de vârstă
grup_v = df.groupby(['an', 'grupa_varsta']).size().reset_index(name='NR_PACIENTI')

# Plot
plt.figure(figsize=(12, 6))
ax = sns.barplot(data=grup_v, x='an', y='NR_PACIENTI', hue='grupa_varsta', palette='Set2')

# Adăugăm etichete cu număr pacienți
for container in ax.containers:
    ax.bar_label(container, fmt='%d', label_type='edge', padding=3)

plt.title("Distribuția pacienților pe ani și grupe de vârstă")
plt.xlabel("An")
plt.ylabel("Număr pacienți")
plt.legend(title="Grupă de vârstă", loc='upper right')
plt.tight_layout()
plt.savefig("distributie_ani_varsta.png")
