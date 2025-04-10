import numpy as np
import pandas as pd

# ---- 1. Load Data  ----
# Standard-Lastprofil für 2019 (stündlich)
file_path = r"D:\Dokumente\Studium\20242025 WS\WattWise\Repo\wattWise\data\slp\GGV_SLP_1000_MWh_2019_01.xlsx"
sheet_name = "15Min - SLP 2019" # Single Load Profile 2019

df_standard_load_profile_2019 = pd.read_excel(file_path, sheet_name=sheet_name)
# 2 Wochen Kundenverbrauch für 2020 (stündlich) -- hier ggf. Input ändern #TODO
#df_random_two_week_customer_load_2020 = pd.read_csv('data/random_two_week_customer_load_2020.csv', sep=';', decimal=',', index_col=0)
df_random_two_week_customer_load_2020 = pd.DataFrame(np.random.rand(24 * 14) * 2, columns=['Customer_Load'])

# Jahresverbrauch des Kunden in kWh
customer_annual_consumption = 3000 # kWh #TODO hier ggf. Input ändern

# ---- 2. Skalierung des Kundenprofils ----
customer_2w_total = df_random_two_week_customer_load_2020['Customer_Load'].sum()

# Skalierungsfaktor berechnen, um auf den Jahresverbrauch zu normieren.
scaling_factor = customer_annual_consumption / (customer_2w_total * 26)
df_random_two_week_customer_load_2020['Scaled_Load'] = df_random_two_week_customer_load_2020['Customer_Load'] * scaling_factor

# ---- 3. Monte-Carlo-Simulation für stündlichen Verbrauch ----
# hier kommt neuer Inpuit aus .ipynb rein #TODO


# Skalierung auf den bekannten Jahresverbrauch nach Anpassung


# ---- 6. Output des finalen DataFrames ----
