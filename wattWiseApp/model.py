# model.py – Datenverarbeitung & Modelllogik (CSV, Lastprofile, PV, Preise)

import base64
import io
import sys
import os
import json
import pandas as pd
from pathlib import Path

# Erlaube Importe aus dem übergeordneten Verzeichnis (z. B. für 'main.py')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from pv_prediction import (
    calculate_net_load_with_pv, 
    load_solar_data_from_csv, 
    get_solar_data_from_api
)

from montecarlo import (
    fill_missing_hours,
    build_weekday_profile_dict,
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

from main import (
    fill_missing_hours,
)

# Lade API-Schlüssel sicher aus secrets.json (nicht im Git!)
root_dir = Path(__file__).resolve().parent.parent # WATTWISE Ebene
secrets_path = root_dir / 'secrets.json'

with open(secrets_path) as f:
    secrets = json.load(f)
ninja_token = secrets.get("ninja_token")
entsoe_api_key = secrets.get("entsoe_api_key")


# 1. Load data from App
def load_csv_as_df(encoded_contents: str) -> pd.DataFrame:
    """
    Decodiert und lädt eine CSV-Datei aus einem base64-kodierten Dash Upload-Inhalt.

    Args:
        encoded_contents (str): Der von Dash übergebene base64-kodierte CSV-Inhalt.

    Returns:
        pd.DataFrame: Das eingelesene DataFrame.
    
    Raises:
        ValueError: Wenn das Einlesen fehlschlägt oder das Format nicht unterstützt wird.
    """
    try:
        _, content_string = encoded_contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=None, engine='python')
        return df
    except Exception as e:
        raise ValueError(f"Fehler beim Einlesen der CSV-Datei: {e}")


def save_dataframe_to_csv(df: pd.DataFrame, filename: str, folder: str = "data") -> str:
    """
    Speichert ein DataFrame als CSV im angegebenen Ordner.

    Args:
        df (pd.DataFrame): Das DataFrame, das gespeichert werden soll.
        filename (str): Der Name der Zieldatei (z. B. "verbrauch.csv").
        folder (str): Zielordner, Standard ist "data".

    Returns:
        str: Der Pfad zur gespeicherten Datei.
    """
    os.makedirs(folder, exist_ok=True)  # Ordner erzeugen, wenn er nicht existiert
    path = os.path.join(folder, filename)
    df.to_csv(path, index=False)
    return path


# 2. Load additional data
def load_and_adjust_standard_load_profile(file_path, sheet_name, time_col = "Time", value_cols: list = ['H00 [kWh]'], fill_value=0, year: int = 2019) -> pd.DataFrame:
    """
    Lädt das Standardlastprofil und passt es an das angegebene Jahr an.

    Args:
        file_path (str): Pfad zur CSV-Datei des Standardlastprofils. file_path = str(root_dir / 'data' / 'slp' / 'GGV_SLP_1000_MWh_2019_01.xlsx')
        sheet_name (str): Name des Arbeitsblatts in der Excel-Datei, das das Lastprofil enthält. Standard ist "15Min - SLP 2019".
        time_col (str): Name der Spalte mit Timestamps. Standard ist "Time".
        value_cols (list): Spalten, die beibehalten/gefüllt werden sollen. Wenn None → alle außer time_col. #hier value_cols=['H00 [kWh]']
        fill_value: Wert zum Auffüllen (z. B. 0, np.nan oder dict).
        year (int): Jahr, für das das Lastprofil angepasst werden soll. Standard ist 2019.

    Returns:
        pd.DataFrame: Angepasstes DataFrame mit dem Standardlastprofil.
    """

    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df_standard_load_profile_2019 = df.copy()

    # Datenaufbereitung
    df_standard_load_profile_2019.drop(columns=['Messwert-Nr.','MP von', 'MP bis'], inplace=True)
    df_standard_load_profile_2019['Time'] = df_standard_load_profile_2019['Zeitstempel von'].dt.floor('h') #Fasse Zeitstempel pro Stunde zusammen und summiere H00 [kW] in neuer df
    df_agg = df_standard_load_profile_2019.groupby('Time').agg({'H00 [kW]': 'sum'}).reset_index()
    df_agg['H00 [kWh]'] = df_agg['H00 [kW]'] / 4 
    df_standard_load_profile_2019 = fill_missing_hours(df_agg, time_col, value_cols, year, fill_value )
    df_standard_load_profile_2019['Load'] = df_standard_load_profile_2019['H00 [kWh]'] /df_standard_load_profile_2019['H00 [kWh]'].sum()*3000 #TODO WOZU?? Normalized Load
    df_standard_load_profile_2019['Weekday'] = df_standard_load_profile_2019['Time'].dt.dayofweek
    df_standard_load_profile_2019['Hour'] = df_standard_load_profile_2019['Time'].dt.hour
    df_standard_load_profile_2019['Seasonal Factor'] = df_standard_load_profile_2019['Load'] / df_standard_load_profile_2019['Load'].mean() #Save an seaonality index for each hour on a annual mean of 1.0 #TODO: Kritisch hinterfragen

    
    return df_standard_load_profile_2019



# 3. Run model pipeline
def run_model_pipeline(hh_name, df, lat, lon, cap, loss, tilt, azimuth,
                       annual_consumption, start_date, end_date,
                       forecast_start, model_choice = "montecarlo") -> dict:
    """
    Führt die gesamte Modellpipeline aus:
    - Simulation des Lastprofils (Monte Carlo)
    - PV-Erzeugung
    - Strompreismodelle (dynamisch + statisch)
    - Kostenschätzung mit & ohne PV

    Args:
        hh_name (str): Name des Haushalts, z. B. "SFH3_P_TOT"
        df (pd.DataFrame): DataFrame mit den zwei Wochen Verbrauchsdaten
        lat (float): Breitengrad
        lon (float): Längengrad
        cap (float): PV-Kapazität in kWp
        loss (float): Systemverluste in Prozent
        tilt (float): Neigungswinkel
        azimuth (float): Azimutwinkel
        annual_consumption (float): Jahresverbrauch in kWh
        start_date (str): Startdatum der Datenbasis für Forecast
        end_date (str): Enddatum der Datenbasis für Forecast (365 Tage später)
        forecast_start (str): Startdatum der Vorhersage
        model_choice (str): Modellwahl. Default ist "montecarlo".

    Returns:
        dict: Ergebnisse wie simulierte Kosten und Fehlermaß.
    """


    #Zeiträume vorbereiten
    start_date_forecast = pd.to_datetime(forecast_start)
    end_date_forecast = start_date_forecast + pd.Timedelta(days=365)
    forecast_year = pd.to_datetime(start_date_forecast).year
    start_date_customer_data = pd.to_datetime(start_date)
    end_date_customer_data = pd.to_datetime(end_date)
    customer_data_year = pd.to_datetime(start_date_customer_data).year


    # Load standard load profile
    slp = load_and_adjust_standard_load_profile(
        file_path = str(root_dir / 'data' / 'slp' / 'GGV_SLP_1000_MWh_2019_01.xlsx'),
        sheet_name="15Min - SLP 2019",
        time_col="Time",
        value_cols=['H00 [kWh]'],
        fill_value=0,
        year=customer_data_year 
    )


    # Load prediction - Verbrauch simulieren (100 MC-Samples)
    weekday_profile_dict = build_weekday_profile_dict(df, timestamp_col='Time', load_col='Load',  mode = 'weekday')
    simulations = load_or_run_simulation(hh_name, weekday_profile_dict, forecast_year, 100, mode = 'weekday')# Lade simulierte Lastprofile aus Cache (wenn vorhanden), oder führe neue Monte-Carlo-Simulation durch 
    seasonal_factor = calculate_seasonal_factor_per_x(slp, x="Month")
    adjusted_simulations = apply_seasonal_factors(simulations, seasonal_factor, by='Month')
    final_simulations = scale_load_profile_to_annual_consumption(adjusted_simulations, annual_consumption) 


    # Load solar data
    #start_date_forecast muss in FOrm YYYY-MM-DD sein, also 2020-01-01, end_date_forecast muss 365 Tage später sein
    start_date_forecast_solar = pd.to_datetime(start_date_forecast).strftime('%Y-%m-%d')
    end_date_forecast_solar = (pd.to_datetime(start_date_forecast) + pd.Timedelta(days=365)).strftime('%Y-%m-%d')
    #Spalten: Time und Electricity
    #Index: Time (UTC)
    solar_df = get_solar_data_from_api(ninja_token, lat, lon, start_date_forecast_solar, end_date_forecast_solar, cap, loss, tilt, azimuth)
    solar_df = load_solar_data_from_csv(root_dir / 'data' / 'renewables_ninja_data' / (f'pv_{start_date_forecast_solar}_{end_date_forecast_solar}_lat{lat}_lon{lon}_cap{cap}.csv'))
    

    #Results
    total_annual_solar_yield = solar_df['Electricity'].sum()
    final_sim_with_pv = [calculate_net_load_with_pv(sim, solar_df) for sim in final_simulations] # wichtig hier final simulations, da diese bereits skaliert sind. Danavh nicht nochmal saklieren, sonst verlieren wir die Einsparung durch PV
    
    #Self-Consumption
    total_loads_with_pv = [sim['Load'].sum() for sim in final_sim_with_pv if 'Load' in sim.columns]
    average_total_load_with_pv = sum(total_loads_with_pv) / len(total_loads_with_pv)
    self_consumption_sim_avg = annual_consumption- average_total_load_with_pv #Jährlicher Verbrauch - Durchschnittliche Last mit PV
    

    # Strompreise laden (ENTSOE Spotmarkt + Fixpreise)
    df_spot_data_requested = load_spot_market_prices(start_date_forecast, start_date_forecast + pd.Timedelta(days=365), country_code = 'DE_LU', data_dir = root_dir / 'data' / 'entsoe_data' / 'normal_hourly', index_new_df_col= 'Time')
    print("df_spot_data_requested.head():", df_spot_data_requested.head())
    df_dynamic_price = calculate_dynamic_price_with_fees(df_spot_data_requested, start_date_forecast, start_date_forecast + pd.Timedelta(days=365))
    
    static_prices_df_2014_2024 = pd.read_csv(root_dir / 'data' / 'electricity_prices_yearly' / 'electricity_prices_yearly2014_2024.csv', delimiter=',', decimal='.', parse_dates=['Year'])
    static_prices_df_2014_2024['Year'] = pd.to_datetime(static_prices_df_2014_2024['Year']).dt.year # Year als Jahreszahl
    
    

    #Claculate costs

    #without PV
    sim_costs = [calculate_annual_dynamic_costs(sim, df_dynamic_price, load_col='Load') for sim in final_simulations]
    sim_costs_round = [round(cost, 2) for cost in sim_costs]
    static_price_per_kwh = get_fixed_price_per_kwh(2020,root_dir / 'data' / 'electricity_prices_yearly' / 'electricity_prices_yearly2014_2024.csv', "Summe")
    sim_costs_static = [calculate_annual_static_costs(sim, static_price_per_kwh, load_col="Load") for sim in final_simulations]
    avg_sim_costs_dynamic = sum(sim_costs) / len(sim_costs)
    avg_sim_costs_static = sum(sim_costs_static) / len(sim_costs_static)

    #with PV
    sim_costs_with_pv = [calculate_annual_dynamic_costs(sim, df_dynamic_price, load_col='Load') for sim in final_sim_with_pv]
    sim_costs_with_pv_round = [round(cost, 2) for cost in sim_costs_with_pv]
    sim_costs_with_pv_static = [calculate_annual_static_costs(sim, static_price_per_kwh, load_col="Load") for sim in final_sim_with_pv]
    avg_sim_costs_dynamic_with_pv = sum(sim_costs_with_pv) / len(sim_costs_with_pv)
    avg_sim_costs_static_with_pv = sum(sim_costs_with_pv_static) / len(sim_costs_with_pv_static)



    #Ergebnis zurückgeben
    return {
        "status": "success",
        "model": model_choice,
        "dynamic_costs_wo_pv_all_sim": sim_costs_round,
        "static_costs_wo_pv_all_sim": sim_costs_static,
        "load_profiles_wo_pv_all_sim": final_simulations,
        "avg_dynamic_costs_wo_pv": avg_sim_costs_dynamic,
        "avg_static_costs_wo_pv": avg_sim_costs_static,

        "load_profiles_w_pv_all_sim": final_sim_with_pv,
        "dynamic_costs_w_pv_all_sim": sim_costs_with_pv_round,
        "static_costs_w_pv_all_sim": sim_costs_with_pv_static,
        "avg_dynamic_costs_w_pv": avg_sim_costs_dynamic_with_pv,
        "avg_static_costs_w_pv": avg_sim_costs_static_with_pv,
        "solar_yield": solar_df,
        "annual solar_yield": total_annual_solar_yield,
        "self_consumption_sim_avg": self_consumption_sim_avg,
    }
