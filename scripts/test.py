import pandas as pd

# 1. Incarca masa master
df = pd.read_excel("master_lot.xlsx")

# 2. Filtreaza
nepr = df[df["CAUZA_DOMINANTA"] == "NEPRECIZAT"]

# 3. Statistica + preview
print("Pacienți cu cauza NEPRECIZAT:", nepr.precod.nunique())
print("\nPrimele 10 coduri + diagnostic:")
print(nepr[["precod", "DIAGNOSTICE"]].head(10))

