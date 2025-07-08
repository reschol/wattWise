import random
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
import numpy as np
import pandas as pd
import json
from pathlib import Path

from src.utils.renewables_ninja import fetch_solar_data
from src.utils.entsoe_client import fetch_and_save_spot_prices

from pv_prediction import (
    calculate_net_load_with_pv, 
    load_solar_data_from_csv, 
    get_solar_data_from_api
)

from montecarlo import (
    fill_missing_hours,
    build_weekday_profile_dict,
    monte_carlo_simulation_load_profiles,
    calculate_seasonal_factor_per_x,
    apply_seasonal_factors,
    scale_load_profile_to_annual_consumption,
    load_spot_market_prices,
    calculate_dynamic_price_with_fees,
    get_fixed_price_per_kwh,
    calculate_annual_dynamic_costs,
    calculate_annual_static_costs,
    load_or_run_simulation
)

from load_prediction_2week_slp import (
    calculate_prediction_model1,
    calculate_prediction_model2,
    scale_load_profile_to_annual_consumption_modelb
)
from customer_input_check import (
    load_pickle_to_dataframe,
    filter_time_range,
    prepare_household_data,
    filter_two_week_data,
    get_household_profile,
)
from evaluation import (
    calculate_nmae_load_forecast_to_actual_load_hourly,
    get_actual_data_from_household_data
)

# Root ermitteln
root_path = Path(__file__).resolve().parent #eine Ebene hoch (zu WATTWISE)


# Define the API tokens
# Personal renewables.ninja API token
with open(root_path / 'secrets.json') as f:
    secrets = json.load(f)

ninja_token = secrets.get("ninja_token")
entsoe_api_key = secrets.get("entsoe_api_key")

#print(ninja_token)

# ninja_token = "" #your renewables.ninja API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
# entsoe_api_key = "" #your entsoe API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
# recommendation: use a JSON file called secrets.json, that is already in the gitignore and should thus be ignored by git

#-----1. Load Data
hh_path = r"local_input_data\1920 Final Data w. Additional Features HH Hourly Agg.pkl"
start_2019 = '2019-01-01'
end_2019 = '2019-12-31'
start_2020 = '2020-01-01'
end_2020 = '2020-12-31'
start_2024 = '2024-01-01'
end_2024 = '2024-12-31'
keyword = 'SFH' # Single Family Households
exclude = ['SFH34_P_TOT'] # weird profile, not usable
data_allhouseholds = load_pickle_to_dataframe(hh_path)
data_2019 = filter_time_range(data_allhouseholds, start_2019, end_2019)
sfh_2019 = prepare_household_data(data_2019, keyword=keyword, exclude_columns=exclude)
#data_2020 = filter_time_range(data_allhouseholds, start_2020, end_2020)
#sfh_2020 = prepare_household_data(data_2020, keyword=keyword, exclude_columns=exclude)
    
#print("Those are the available household loads in 2019:")
#print(sfh_2019.head())

#--a) Filter the data for a two-week period in 2019
#random_start_date = random.choice(pd.date_range(pd.Timestamp(start_2019), pd.Timestamp(end_2019) - pd.Timedelta(days=14), tz='UTC'))
#random_end_date = random_start_date + pd.Timedelta(days=14)
random_start_date = '2019-01-01 00:00:00+00:00' #TODO : random choice
random_end_date = '2019-01-15 00:00:00+00:00' #TODO : random choice
testhousehold = 'SFH4_P_TOT' #TODO: alle HH 


two_week_data = filter_two_week_data(sfh_2019, random_start_date, random_end_date)
    
print("Filtered two-week data:", two_week_data)
random_household_two_week = get_household_profile(two_week_data, testhousehold)

print("Household profile", testhousehold," for two weeks:", random_household_two_week)

#--b) Load Standard Load Profile (SLP) data for 2019

file_path = str(root_path / 'data' / 'slp' / 'GGV_SLP_1000_MWh_2019_01.xlsx')
sheet_name = "15Min - SLP 2019" # Single Load Profile 2019
df_standard_load_profile_2019 = pd.read_excel(file_path, sheet_name=sheet_name)

def fill_missing_hours(df: pd.DataFrame, time_col: str = "Time", value_cols: list = None,
                       year: int = 2019, fill_value=None) -> pd.DataFrame:
    """
    Erkennt fehlende Stunden in einem Zeitreihen-DataFrame und füllt sie optional mit fill_value (z. B. 0 oder NaN).

    Args:
        df (DataFrame): Zeitreihen-DataFrame mit einer Zeitspalte.
        time_col (str): Name der Spalte mit Timestamps.
        value_cols (list): Spalten, die beibehalten/gefüllt werden sollen. Wenn None → alle außer time_col.
        year (int): Jahr, für das die Stunden geprüft werden sollen.
        fill_value: Wert zum Auffüllen (z. B. 0, np.nan oder dict).

    Returns:
        DataFrame mit allen 8760 Stunden (oder 8784 bei Schaltjahr), vollständig aufgefüllt.
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df.set_index(time_col, inplace=True)

    # Generiere kompletten Stundenindex für das Jahr
    start = f"{year}-01-01 00:00"
    end = f"{year}-12-31 23:00"
    full_index = pd.date_range(start=start, end=end, freq="h")

    # Bestimme Spalten
    if value_cols is None:
        value_cols = [col for col in df.columns if col != time_col]

    # Reindex & auffüllen
    df_full = df.reindex(full_index)

    if fill_value is not None:
        df_full[value_cols] = df_full[value_cols].fillna(fill_value)

    df_full.reset_index(inplace=True)
    df_full.rename(columns={"index": time_col}, inplace=True)

    return df_full

#--c) Actual Load Daten Laden
#TODO: Start date
#TODO: End date
#TODO: Funktion answenden actual_load_household = get_actual_data_from_household_data(sfh_2019, actual_start_date, actual_end_date, load_col=testhousehold)
#TODO: nächste Zeile löschen
actual_load = pd.read_csv(root_path / 'data' / 'test_data_actual_load_profile_2020.csv', sep=',', index_col='date')
#only testhousehold ('SFHx_P_TOT') and date
actual_load_household = actual_load[[testhousehold]]
actual_load_household.index = pd.to_datetime(actual_load_household.index)
actual_load_household.index = actual_load_household.index.tz_convert(None)



#Anpassen
df_standard_load_profile_2019.drop(columns=['Messwert-Nr.','MP von', 'MP bis'], inplace=True)
df_standard_load_profile_2019['Time'] = df_standard_load_profile_2019['Zeitstempel von'].dt.floor('h') #Fasse Zeitstempel pro Stunde zusammen und summiere H00 [kW] in neuer df
df_agg = df_standard_load_profile_2019.groupby('Time').agg({'H00 [kW]': 'sum'}).reset_index()
df_agg['H00 [kWh]'] = df_agg['H00 [kW]'] / 4 
df_standard_load_profile_2019 = fill_missing_hours(df=df_agg, time_col='Time', value_cols=['H00 [kWh]'],
    year=2019,
    fill_value=0 # oder np.nan
)
df_standard_load_profile_2019['Load'] = df_standard_load_profile_2019['H00 [kWh]'] /df_standard_load_profile_2019['H00 [kWh]'].sum()*3000 #TODO WOZU?? Normalized Load
df_standard_load_profile_2019['Weekday'] = df_standard_load_profile_2019['Time'].dt.dayofweek
df_standard_load_profile_2019['Hour'] = df_standard_load_profile_2019['Time'].dt.hour
df_standard_load_profile_2019['Seasonal Factor'] = df_standard_load_profile_2019['Load'] / df_standard_load_profile_2019['Load'].mean() #Save an seaonality index for each hour on a annual mean of 1.0 #TODO: Kritisch hinterfragen

#--d) Load Spot Market Prices
country_code = 'DE_LU'  # 'DE_LU' for 2018 - 2023 and 'DE_AT_LU' for < 2018
spot_directory = 'data/entsoe_data/normal_hourly' #wenn daten bereits abgefragt wurden, sonst über API
entsoe_api_key = secrets.get("entsoe_api_key")
#EntsoE API call
#fetch_and_save_spot_prices(entsoe_api_key, country_code, start_2024, end_2024, spot_directory)


# PV Prediciton
def load_or_fetch_solar_data(csv_path, ninja_token, lat=50.0, lon=8.0, start='2021-01-01', end='2021-12-30', capacity=0.8, loss=0.1, tilt=90, azim=180):
        """
        Loads solar data from CSV if available, otherwise fetches from API and returns the DataFrame.
        """
        try:
            solar_df = load_solar_data_from_csv(csv_path)
            print("Solar data loaded from CSV.")
        except FileNotFoundError:
            print("File not found, fetching from API.")
            solar_df = get_solar_data_from_api(ninja_token, lat, lon, start, end, capacity, loss, tilt, azim)
        return solar_df

def main():
    global country_code, spot_directory

    # Load dynamic electricity price
    df_spot_data_requested = load_spot_market_prices(start_2020, end_2020, country_code, spot_directory)
    df_dynamic_price = calculate_dynamic_price_with_fees(df_spot_data_requested, start_2020, end_2020)
    
    # Lade PV-Erzeugungsdaten
    csv_path = 'data/renewables_ninja_data/pv_Karlsruhe_2020.csv'
    solar_df = load_or_fetch_solar_data(csv_path, ninja_token)



    # Datenstruktur vorbereiten
    #ohne PV
    all_simulated_costs = []
    actual_costs = []
    household_labels = []
    household_nmae_means_monte_carlo = []
    household_nmae_stds_monte_carlo = []
    household_dyn_costs_monte_carlo = []
    household_nmae_modelb1 = []	
    household_dyn_costs_modelb1 = []
    household_nmae_modelb2 = []
    household_dyn_costs_modelb2 = []
    household_actual_costs = []
  

    # mit PV
    household_actual_costs_pv = []
    #all_simulated_costs_pv = []
    household_dyn_costs_monte_carlo_pv = []
    household_dyn_costs_modelb1_pv = []
    household_dyn_costs_modelb2_pv = []
    household_nmae_means_monte_carlo_pv = []
    household_nmae_stds_monte_carlo_pv = []
    household_nmae_modelb1_pv = []	
    household_nmae_modelb2_pv = []

    
    for household_col in sfh_2019.columns:
        household_labels.append(household_col)

        # 2-Wochen-Profil 
        two_week_data = filter_two_week_data(sfh_2019, random_start_date, random_end_date)
        random_household_two_week = get_household_profile(two_week_data, household_col)

        # Load actual values
        actual_load_household = actual_load[[household_col]]
        actual_load_household.index = pd.to_datetime(actual_load_household.index)
        actual_load_household.index = actual_load_household.index.tz_convert(None)

        #----- Model comparison: Model A - Monte Carlo -----------
        # Model Monte Carlo Simulation
        weekday_profile_dict = build_weekday_profile_dict(random_household_two_week, timestamp_col='Time', load_col='Load',  mode = 'weekday')
        simulations = load_or_run_simulation(household_col, weekday_profile_dict, 2020, 100, mode = 'weekday')# Lade simulierte Lastprofile aus Cache (wenn vorhanden), oder führe neue Monte-Carlo-Simulation durch #TODO: Jahr unabhängig machen
        seasonal_factor = calculate_seasonal_factor_per_x(df_standard_load_profile_2019, x="Month")
        adjusted_simulations = apply_seasonal_factors(simulations, seasonal_factor, by='Month')
        final_simulations = scale_load_profile_to_annual_consumption(adjusted_simulations, 3000)

        # a) Plot mit Details für einen spezifischen Haushalt
        if household_col == "x": #TODO: x durch den gewünschten Haushalt ersetzen, wenn Plot gewünscht ist
            plt.figure(figsize=(12, 6))
            hours = 720  # 30 Tage
            for sim in final_simulations:
                index_profile = sim.head(hours)
                plt.plot(index_profile.index, index_profile['Load'], alpha=0.2, linewidth=1)
            actual_slice = actual_load_household.loc[actual_load_household.index[:hours]]
            plt.plot(actual_slice.index, actual_slice[household_col], color='red', label='Actual Load', linewidth=1)
            plt.title(f"First {hours} Hours of 100 Simulated Load Profiles – {household_col}")
            plt.xlabel("Time")
            plt.ylabel("Load [kWh]")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()

        # b) Berechne Kosten
        sim_costs = [
            calculate_annual_dynamic_costs(sim, df_dynamic_price, load_col='Load') for sim in final_simulations
        ]
        household_dyn_costs_monte_carlo.append(np.mean(sim_costs))

        actual_cost = calculate_annual_dynamic_costs(actual_load_household, df_dynamic_price, load_col=household_col)
        household_actual_costs.append(actual_cost)


        # Berechne NMAE
        nmae_load_list = []
        for sim in final_simulations:
            sim = sim[:-24]  # Letzte 24h entfernen
            nmae = calculate_nmae_load_forecast_to_actual_load_hourly(sim, actual_load_household,
                                                                       load_forecast_col='Load',
                                                                       actual_load_col=household_col)
            nmae_load_list.append(nmae)

        household_nmae_means_monte_carlo.append(np.mean(nmae_load_list))
        household_nmae_stds_monte_carlo.append(np.std(nmae_load_list))

        # Speichern
        all_simulated_costs.append(sim_costs)
        actual_costs.append(actual_cost)
        
    
    #----- Model comparison: Model B1 - Just two week customer household data -----------
        predictions_modelb1 = calculate_prediction_model1(
            random_household_two_week,
            random_start_date,
            random_end_date,
            start_2020,
            end_2020,
            timestamp_col = 'Time',
            load_col = 'Load'
        )
        # Normalisiere die Vorhersage auf den jährlichen Verbrauch
        final_predictions_modelb1 = scale_load_profile_to_annual_consumption_modelb(predictions_modelb1, 3000)
        # a) Plot mit Details für einen spezifischen Haushalt #TODO
        
        # b) Berechne Kosten
        costs_modelb1 = calculate_annual_dynamic_costs(final_predictions_modelb1, df_dynamic_price, load_col='Load')
        household_dyn_costs_modelb1.append(costs_modelb1)
        # c) Berechne NMAE
        nmae_load_modelb1 = calculate_nmae_load_forecast_to_actual_load_hourly(final_predictions_modelb1, actual_load_household, load_forecast_col='Load', actual_load_col=household_col)
        household_nmae_modelb1.append(nmae_load_modelb1)

    #----- Model comparison: Model B2 - SLP and two week customer data set -----------
        predictions_modelb2 = calculate_prediction_model2(
            df_standard_load_profile_2019,
            random_household_two_week,
            random_start_date,
            random_end_date,
            start_2020,
            end_2020,
            timestamp_col = 'Time',
            load_col = 'Load',
            weight_season_twoweek = 0.7,
            weight_season_slp = 0.3,
            weight_offseason_twoweek = 0.5,
            weight_offseason_slp = 0.5
        )
        # Normalisiere die Vorhersage auf den jährlichen Verbrauch
        final_predictions_modelb2 = scale_load_profile_to_annual_consumption_modelb(predictions_modelb2, 3000)
        # a) Plot mit Details für einen spezifischen Haushalt #TODO
        
        # b) Berechne Kosten
        costs_modelb2 = calculate_annual_dynamic_costs(final_predictions_modelb2, df_dynamic_price, load_col='Load')
        household_dyn_costs_modelb2.append(costs_modelb2)

        # c) Berechne NMAE
        nmae_load_modelb2 = calculate_nmae_load_forecast_to_actual_load_hourly(final_predictions_modelb2, actual_load_household, load_forecast_col='Load', actual_load_col=household_col)
        household_nmae_modelb2.append(nmae_load_modelb2)
        
    #----- Integrate PV in all three models -----------
        # Actual Load with PV

        actual_load_with_pv_df = calculate_net_load_with_pv(actual_load_household, solar_df, load_df_col=household_col)
        
        actual_cost_pv = calculate_annual_dynamic_costs(actual_load_with_pv_df, df_dynamic_price, load_col='Load')
        household_actual_costs_pv.append(actual_cost_pv)
        
        
        
        # Model MC: Monte Carlo Simulation - Costs und NMAE
        nmae_load_list_pv = []
        for sim in final_simulations:
            load_with_pv_df_mc = calculate_net_load_with_pv(sim, solar_df)
            #TODO: load_with_pv_df_mc = load_with_pv_df_mc[:-24]  # Letzte 24h entfernen -> unschön. load_with_pv_df_mc hat sonst Tage bis 31. 12.2020, actual_load_with_pv_df hat nur bis 30.12.2020. Dies muss gleich sein
            load_with_pv_df_mc_short = load_with_pv_df_mc[:-24]
            
            nmae_pv = calculate_nmae_load_forecast_to_actual_load_hourly(load_with_pv_df_mc_short, actual_load_with_pv_df,load_forecast_col='Load',
                                                                       actual_load_col=household_col)
            nmae_load_list_pv.append(nmae_pv)
            sim_costs = [
                calculate_annual_dynamic_costs(load_with_pv_df_mc, df_dynamic_price, load_col='Load') 
            ]
        household_dyn_costs_monte_carlo_pv.append(np.mean(sim_costs))
        household_nmae_means_monte_carlo_pv.append(np.mean(nmae_load_list_pv))
        household_nmae_stds_monte_carlo_pv.append(np.std(nmae_load_list_pv))
 
        # Model B1
        final_predictions_modelb1_pv = calculate_net_load_with_pv(final_predictions_modelb1, solar_df)
        costs_modelb1_pv = calculate_annual_dynamic_costs(final_predictions_modelb1_pv, df_dynamic_price, load_col='Load')
        household_dyn_costs_modelb1_pv.append(costs_modelb1_pv)

        nmae_load_modelb1_pv = calculate_nmae_load_forecast_to_actual_load_hourly(final_predictions_modelb1_pv, actual_load_with_pv_df, load_forecast_col='Load', actual_load_col=household_col)
        household_nmae_modelb1_pv.append(nmae_load_modelb1_pv)

        # Model B2
        final_predictions_modelb2_pv = calculate_net_load_with_pv(final_predictions_modelb2, solar_df)
        costs_modelb2_pv = calculate_annual_dynamic_costs(final_predictions_modelb2_pv, df_dynamic_price, load_col='Load')
        household_dyn_costs_modelb2_pv.append(costs_modelb2_pv)

        nmae_load_modelb2_pv = calculate_nmae_load_forecast_to_actual_load_hourly(final_predictions_modelb2_pv, actual_load_with_pv_df, load_forecast_col='Load', actual_load_col=household_col)
        household_nmae_modelb2_pv.append(nmae_load_modelb2_pv)
    

    #Boxplot
    plt.figure(figsize=(15, len(household_labels) * 0.5 + 3))
    bplot = plt.boxplot(all_simulated_costs, vert=False, patch_artist=True,
                        boxprops=dict(facecolor='lightblue'),
                        medianprops=dict(color='black'))
    for i, cost in enumerate(actual_costs):
        plt.plot(cost, i + 1, 'rD', label='Actual' if i == 0 else "")  # nur 1x label
    plt.yticks(ticks=np.arange(1, len(household_labels) + 1), labels=household_labels)
    plt.xlabel("Annual Dynamic Costs [€]")
    plt.title(" Model A: Monte Carlo Annual Dynamic Cost Distribution – All Households")
    plt.grid(axis='x', alpha=0.3)
    plt.legend(loc='upper right')
    plt.tight_layout()
    #plt.show()
    
    #Zusammenfassung der NMAE-Werte
    nmae_summary = pd.DataFrame({
        "Household": household_labels,
        "Mean NMAE Monte Carlo": household_nmae_means_monte_carlo,
        "Std NMAE Monte Carlo": household_nmae_stds_monte_carlo,
        "Mean NMAE Model B1": household_nmae_modelb1,
        "Mean NMAE Model B2": household_nmae_modelb2
    })
    print("\n--- NMAE Summary ---")
    print(nmae_summary.round(4))
    print("\nOverall Mean NMAE Monte Carlo:", np.mean(household_nmae_means_monte_carlo))
    print("Overall Std NMAE Monte Carlo:", np.std(household_nmae_means_monte_carlo))
    print("\n Mean NMAE Model B1", np.mean(household_nmae_modelb1))
    print("Mean Std NMAE Model B1", np.std(household_nmae_modelb1))
    print("\n Mean NMAE Model B2", np.mean(household_nmae_modelb2))
    print("Mean Std NMAE Model B2", np.std(household_nmae_modelb2))


    #Zusammenfassung der NMAE-Werte MIT PV
    nmae_summary_pv = pd.DataFrame({
        "Household": household_labels,
        "Mean NMAE Monte Carlo with PV": household_nmae_means_monte_carlo_pv,
        "Std NMAE Monte Carlo with PV": household_nmae_stds_monte_carlo_pv,
        "Mean NMAE Model B1 with PV": household_nmae_modelb1_pv,
        "Mean NMAE Model B2 with PV": household_nmae_modelb2_pv
    })

    print("\n--- NMAE Summary WITH PV ---")
    print(nmae_summary_pv.round(4))
    print("\nOverall Mean NMAE Monte Carlo:", np.mean(household_nmae_means_monte_carlo_pv))
    print("Overall Std NMAE Monte Carlo:", np.std(household_nmae_means_monte_carlo_pv))
    print("\n Mean NMAE Model B1", np.mean(household_nmae_modelb1_pv))
    print("Mean Std NMAE Model B1", np.std(household_nmae_modelb1_pv))
    print("\n Mean NMAE Model B2", np.mean(household_nmae_modelb2_pv))
    print("Mean Std NMAE Model B2", np.std(household_nmae_modelb2_pv))


    #Zusammenfassung der Kosten
    costs_summary = pd.DataFrame({
        "Household": household_labels,
        "Mean Annual Dyn. Costs MC": [np.mean(costs) for costs in all_simulated_costs],
        "Std Annual Dyn. Costs MC": [np.std(costs) for costs in all_simulated_costs],
        "Annual Dyn. Costs Model B1": household_dyn_costs_modelb1,
        "Annual Dyn. Costs Model B2": household_dyn_costs_modelb2,
        "Actual Annual Dyn. Costs": household_actual_costs
    })
    average_all_households_mc = np.mean([np.mean(costs) for costs in all_simulated_costs])
    average_all_households_modelb1 = np.mean(household_dyn_costs_modelb1)
    average_all_households_modelb2 = np.mean(household_dyn_costs_modelb2)
    average_all_households_actual = np.mean(household_actual_costs)
    print("------------ Price Summary -----")
    print(costs_summary.round(4))
    print("\nOverall Mean Annual Dynamic Costs Monte Carlo:", average_all_households_mc)
    print("\nOverall Mean Annual Dynamic Costs Model B1:", average_all_households_modelb1)    
    print("\nOverall Mean Annual Dynamic Costs Model B2:", average_all_households_modelb2)
    print("\nOverall Mean Annual Dynamic Costs Actual:", average_all_households_actual)

    #Liniendiagramm PReisvergleiche der Models und der tatsächlichen Kosten
    plt.figure(figsize=(12, 6))
    plt.plot(household_labels, household_dyn_costs_monte_carlo, label='Monte Carlo', marker='o', color='blue')
    plt.plot(household_labels, household_dyn_costs_modelb1, label='Model B1', marker='o', color='orange')
    plt.plot(household_labels, household_dyn_costs_modelb2, label='Model B2', marker='o', color='green')
    plt.plot(household_labels, household_actual_costs, label='Actual', marker='o', color='red', linestyle='--')
    plt.title("Annual Dynamic Costs Comparison")
    plt.xlabel("Household")
    plt.ylabel("Annual Dynamic Costs [€]")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

    #Zusammenfassung der Kosten mit 
    costs_summary_pv = pd.DataFrame({
        "Household": household_labels,
        "Mean Annual Dyn. Costs MC with PV": household_dyn_costs_monte_carlo_pv,
        "Annual Dyn. Costs Model B1 with PV": household_dyn_costs_modelb1_pv,
        "Annual Dyn. Costs Model B2 with PV": household_dyn_costs_modelb2_pv,
        "Actual Annual Dyn. Costs with PV": household_actual_costs_pv
    })
    average_all_households_mc_pv = np.mean(household_dyn_costs_monte_carlo_pv)
    average_all_households_modelb1_pv = np.mean(household_dyn_costs_modelb1_pv)
    average_all_households_modelb2_pv = np.mean(household_dyn_costs_modelb2_pv)
    average_all_households_actual_pv = np.mean(household_actual_costs_pv)


    print("------------ Price Summary with PV -----")
    print(costs_summary_pv.round(4))
    print("\nOverall Mean Annual Dynamic Costs Monte Carlo with PV:", average_all_households_mc_pv)
    print("\nOverall Mean Annual Dynamic Costs Model B1 with PV:", average_all_households_modelb1_pv)
    print("\nOverall Mean Annual Dynamic Costs Model B2 with PV:", average_all_households_modelb2_pv)
    print("\nOverall Mean Annual Dynamic Costs Actual with PV:", average_all_households_actual_pv)
   
    #Liniendiagramm PReisvergleiche der Models und der tatsächlichen Kosten
    plt.figure(figsize=(12, 6))
    plt.plot(household_labels, household_dyn_costs_monte_carlo_pv, label='Monte Carlo', marker='o', color='blue')
    plt.plot(household_labels, household_dyn_costs_modelb1_pv, label='Model B1', marker='o', color='orange')
    plt.plot(household_labels, household_dyn_costs_modelb2_pv, label='Model B2', marker='o', color='green')
    plt.plot(household_labels, household_actual_costs_pv, label='Actual', marker='o', color='red', linestyle='--')
    plt.title("Annual Dynamic Costs Comparison WITH PV")
    plt.xlabel("Household")
    plt.ylabel("Annual Dynamic Costs [€]")
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

       
    #EntsoE API call
    #fetch_and_save_spot_prices(entsoe_api_key, country_code, start_date, end_date, spot_directory)
    
    #Renewables Ninja API call
    #solar_data = fetch_solar_data(ninja_token, 50.0, 8.0, '2021-01-01', '2021-12-31',1,0.1,90,180)
    #print(solar_data)
     


if __name__ == "__main__":
    main()
    
