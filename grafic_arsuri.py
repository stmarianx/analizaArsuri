import pandas as pd
import matplotlib.pyplot as plt

# Incarca datele
df = pd.read_excel("cauze_arsuri.xlsx")

# Selecteaza coloanele cauzale
coloane_cauze = ['flacara', 'lichid', 'contact', 'electrocutie', 'chimica', 'solara', 'explozie']
distributie = df[coloane_cauze].sum().sort_values(ascending=False)

# Creeaza graficul
plt.figure(figsize=(10, 6))
bars = plt.bar(distributie.index.str.capitalize(), distributie.values, color='coral')
plt.title("Distribuție cauze posibile ale arsurilor (aparitii totale)")
plt.ylabel("Număr apariții")
plt.xlabel("Cauză")
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Etichete pe bare
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height + 10, str(int(height)),
             ha='center', va='bottom', fontsize=9)

# Salveaza imaginea in fisier PNG
plt.tight_layout()
plt.savefig("distributie_cauze_arsuri.png", dpi=300)
