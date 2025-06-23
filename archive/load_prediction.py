#Import
import pandas as pd
import json
from pathlib import Path
from src.utils.entsoe_client import fetch_and_save_spot_prices


# Load Spot Prices from CSV 
def load_spot_prices(year: int, entsoe_api_key, country_code) -> pd.DataFrame:
    """
    Lädt und verarbeitet Strompreisdaten für ein bestimmtes Jahr aus der data/entsoe_data/normal_hourly/Spot_prices_DE_LU_{year}.csv

    Args:
        year (int): Jahr (z. B. 2019 oder 2020)

    Returns:
        DataFrame mit Strompreisen in ct/kWh.
    """

    # Check if the file exists, if not, raise an error and load it from the API fetch_and_save_spot_prices(entsoe_api_key, country_code, start_date, end_date, spot_directory)
    filepath = Path(f"data/entsoe_data/normal_hourly/Spot_prices_DE_LU_{year}.csv")
    if not filepath.exists():
        print(f"Datei nicht gefunden. Wir speichern die Daten für {year}...")
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        spot_directory = 'data/entsoe_data/normal_hourly'
        fetch_and_save_spot_prices(entsoe_api_key, country_code, start_date, end_date, spot_directory)
        df_spot_price = pd.read_csv(
            filepath,
            delimiter=';',
            decimal=',',
            parse_dates=['Date (CET)'],
            dayfirst=True
            )
        df_spot_price['Price ct/KWH'] = df['Price (€/MWh)'].apply(lambda x: x / 1000 * 100)
    else: 
        df_spot_price = pd.read_csv(
            filepath,
            delimiter=';',
            decimal=',',
            parse_dates=['Date (CET)'],
            dayfirst=True
            )
        df_spot_price['Price ct/KWH'] = df['Price (€/MWh)'].apply(lambda x: x / 1000 * 100)
    return df_spot_price


#load_household_data




#load standard load profile


# Zwei Wochen Lastprofil erstellen für MonteCarlo Simulation


#MonteCarlo Simulation für Lastprofil erstellen mit Outout load_df






#Test
with open(r"D:\Dokumente\Studium\20242025 WS\WattWise\Repo\wattWise\secrets.json") as f:
    secrets = json.load(f)
entsoe_api_key = secrets.get("entsoe_api_key")
df = load_spot_prices(2019, entsoe_api_key, 'DE_LU')
print(df.head())
