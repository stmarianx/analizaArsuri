import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel("pacienti_cu_procente.xlsx")

# Categorii de procente
bins = [0, 10, 30, 50, 70, 90, 100]
labels = ['0–10%', '11–30%', '31–50%', '51–70%', '71–90%', '91–100%']
df['categorie_procente'] = pd.cut(df.iloc[:, -1], bins=bins, labels=labels, include_lowest=True)

# Distributie
distributie = df['categorie_procente'].value_counts().sort_index()

# Grafic
plt.figure(figsize=(8, 6))
bars = plt.bar(distributie.index, distributie.values, color='cornflowerblue', edgecolor='black')
plt.title("Distribuția pacienților în funcție de suprafața corporală arsă")
plt.xlabel("Procent suprafață arsă")
plt.ylabel("Număr pacienți")
plt.xticks(rotation=0)  # <-- aici e modificarea
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("distributie_procente_arsuri.png")
