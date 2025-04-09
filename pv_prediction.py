import json
import pandas as pd
import numpy as np
from src.utils.renewables_ninja import fetch_solar_data




def get_solar_data_from_api(ninja_token, lat: float, lon: float, start: str, end: str,
                            capacity: float = 0.8, system_loss: float = 0.1,
                            tilt: int = 90, azimuth: int = 180) -> pd.DataFrame:
    """
    Holt Solar-Daten von Renewables.ninja API.

    Parameters:
        ninja_token (str): API-Token für Renewables.ninja.
        lat (float): Breitengrad. 50.0 # Karlsruhe
        lon (float): Längengrad. 8.0 # Karlsruhe
        start (str): Startdatum im Format 'YYYY-MM-DD'.
        end (str): Enddatum im Format 'YYYY-MM-DD'. # nur bis zum 30., da 2020 ein Schaltjahr war, und wir sonst nicht auf 365 Tage kommen
        capacity (float): Kapazität der PV-Anlage in kW. Default ist 0.8 kW. 
        system_loss (float): Systemverluste in %. Default ist 10%.
        tilt (int): Neigungswinkel der PV-Anlage in Grad. Default ist 90°.
        azimuth (int): Azimutwinkel der PV-Anlage in Grad. Default ist 180°.

    Returns:
        DataFrame: PV-Erzeugung.
    """
    
    raw_data = fetch_solar_data(
        token=ninja_token,
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        capacity=capacity,
        system_loss=system_loss,
        tilt=tilt,
        azimuth=azimuth
    )
    df = raw_data[0]

    #make Time column the index and tz-aware
    df.to_csv('data/renewables_ninja_data/pv_Karlsruhe_2020.csv', index=True)
    df = df.set_index('Time')
    df.index = df.index.tz_localize('UTC')
    return df

def load_solar_data_from_csv(filepath: str) -> pd.DataFrame:
    """
    CSV-Datei der PV-Daten einlesen und index als zeitzonenbewusst setzen.

    Parameters:
        filepath (str): Pfad zur CSV-Datei.

    Returns:
        DataFrame: PV-Daten.
    """
    df = pd.read_csv(filepath, index_col='Time', parse_dates=True)
    return df

def calculate_net_load_with_pv(load_df, solar_df):
    """
    Berechnet den tatsächlichen Stromverbrauch unter Berücksichtigung der PV-Anlage.

    Parameters:
        load_df (DataFrame): Stromverbrauch des Haushalts.
        solar_df (DataFrame): Erzeugte Solarenergie.

    Returns:
        DataFrame: Nettoverbrauch (Strombedarf abzüglich PV-Erzeugung).
    """
    load_with_pv_df = load_df.copy()
    load_with_pv_df['Net_Load'] = load_df['Load'].sub(solar_df['Electricity'], fill_value=0)
    load_with_pv_df['Net_Load'] = load_with_pv_df['Net_Load'].apply(lambda x: max(x, 0))
    return load_with_pv_df


