import numpy as np
import pandas as pd

# ---- 1. Load Data  ----
# Standard-Lastprofil für 2019 (stündlich)
df_standard_load_profile_2019 = pd.read_csv('data/standard_load_profile_2019.csv', sep=';', decimal=',', index_col=0)

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
np.random.seed(42) #damit die Simulation reproduzierbar ist
monte_carlo_simulations = 100 # Anzahl der Simulationen
simulated_profiles = [] # Liste für die simulierten Profile

for _ in range(monte_carlo_simulations):
    noise = np.random.normal(0, 0.1, size=df_random_two_week_customer_load_2020.shape[0]) # Normalverteiltes Rauschen
    simulated_profiles.append(df_random_two_week_customer_load_2020['Scaled_Load'] + noise) # Skaliertes Profil + Rauschen

df_simulated = pd.DataFrame(simulated_profiles).mean(axis=0)  # Mittelwert der simulierten Profile

# Wiederholen des 2-wöchigen Profils für das ganze Jahr
predicted_full_year_load = pd.concat([df_simulated] * 26, ignore_index=True) #TODO überprüfen, ob 26 stimmt, und ob Logik stimmt

# ---- 4. Anpassung an saisonale Schwankungen aus Standardlastprofil ----
# Normierung des Standardlastprofils auf Mittelwert 1
seasonality_factor = df_standard_load_profile_2019['Standard_Load'] / df_standard_load_profile_2019['Standard_Load'].mean()

# Anwendung des saisonalen Faktors auf die Prognose
predicted_full_year_load *= seasonality_factor.values

# Skalierung auf den bekannten Jahresverbrauch nach Anpassung
scaling_factor_final = customer_annual_consumption / predicted_full_year_load.sum()
predicted_full_year_load *= scaling_factor_final

# ---- 6. Erstellung des finalen DataFrames ----
date_range = pd.date_range(start='2020-01-01', periods=8760, freq='H', tz='UTC')
df_customer_load_full_year = pd.DataFrame({'Datetime': date_range, 'Predicted_Consumption': predicted_full_year_load})
df_customer_load_full_year.set_index('Datetime', inplace=True)
