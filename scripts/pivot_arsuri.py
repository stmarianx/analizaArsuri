# -*- coding: utf-8 -*-
"""
Script: pivot_extins_arsuri.py
Scop:   Combina datele clinice, completeaza lipsurile si genereaza
        un pivot cu media zilelor de spital si numarul de pacienti unici
        pe fiecare combinatie (cauza, interval %, tratament, stare externare).
"""

import pandas as pd
import numpy as np
import time

# ------------------------------------------------------------------
t_total = time.time()

print("1) Incarc fisierele ...")
df_baza     = pd.read_excel("baza_date_completa.xlsx")
df_cauze    = pd.read_excel("cauze_arsuri.xlsx")
df_procente = pd.read_excel(
    "pacienti_cu_procente.xlsx",
    usecols=[
        "precod",
        "DATA_INTERNARE",
        "DATA_EXTERNARE",
        "PROCENT_SUPRAF_ARS",
        "TIP_EXTERNARE",
    ],
)
print("   -> OK\n")

# ------------------------------------------------------------------
print("2) Merge ...")
df = (
    df_baza.merge(df_cauze, on="precod", how="left")
           .merge(df_procente, on="precod", how="left")
)
print("   -> OK\n")

# ------------------------------------------------------------------
print("3) Prelucrez coloane ...")

# a) Cauza dominanta
cauze_cols = [
    "flacara",
    "lichid",
    "contact",
    "electrocutie",
    "chimica",
    "solara",
    "explozie",
]

def cauza_dominanta(row):
    if row[cauze_cols].max() > 0:
        return row[cauze_cols].idxmax()
    return "NEPRECIZAT"

df["CAUZA_DOMINANTA"] = df.apply(cauza_dominanta, axis=1)

# b) Interval procent ars
bins   = [0, 10, 30, 50, 70, 90, 100]
labels = ["0–10%", "11–30%", "31–50%", "51–70%", "71–90%", "91–100%"]
df["PROCENT_INTERVAL"] = pd.cut(
    df["PROCENT_SUPRAF_ARS"], bins=bins, labels=labels, include_lowest=True
).astype(str).fillna("NEPRECIZAT")

# c) Zile spital
df["DATA_INTERNARE"] = pd.to_datetime(df["DATA_INTERNARE"], errors="coerce")
df["DATA_EXTERNARE"] = pd.to_datetime(df["DATA_EXTERNARE"], errors="coerce")
df["ZILE_SPITAL"] = (df["DATA_EXTERNARE"] - df["DATA_INTERNARE"]).dt.days

# d) Tratament si stare externare
df["TRATAMENT"]       = df["TRATAMENT"].fillna("NEPRECIZAT")
df["STARE_EXTERNARE"] = df["TIP_EXTERNARE"].fillna("Necunoscut").str.upper()

print("   -> OK\n")

# ------------------------------------------------------------------
print("4) Generez pivot ...")

pivot_mean = pd.pivot_table(
    df,
    values="ZILE_SPITAL",
    index=[
        "CAUZA_DOMINANTA",
        "PROCENT_INTERVAL",
        "TRATAMENT",
        "STARE_EXTERNARE",
    ],
    aggfunc="mean",
).rename(columns={"ZILE_SPITAL": "ZILE_SPITAL_MEDIE"}).round(1)

pivot_count = pd.pivot_table(
    df,
    values="precod",
    index=[
        "CAUZA_DOMINANTA",
        "PROCENT_INTERVAL",
        "TRATAMENT",
        "STARE_EXTERNARE",
    ],
    aggfunc="nunique",
).rename(columns={"precod": "NR_PACIENTI_UNICI"})

pivot = pivot_mean.join(pivot_count).reset_index()

print("   -> OK\n")

# ------------------------------------------------------------------
print("5) Salvez ...")
pivot.to_excel("pivot_extins_arsuri.xlsx", index=False)
print("   -> Salvare completa")

print(f"\nScript finalizat in {round(time.time() - t_total, 2)} secunde ✅")
