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
        DataFrame: PV-Erzeugung. Einheit:  .
    """
    
    raw_data = fetch_solar_data(
       ninja_token,
        lat,
        lon,
        start,
        end,
        capacity,
        system_loss,
        tilt,
        azimuth
    )
    df = raw_data[0]
    print(df.head(24))

    #make Time column the index and tz-aware
    #df = df.set_index('Time')
    #df.index = df.index.tz_localize('UTC')
    df.to_csv(f'data/renewables_ninja_data/pv_{start}_{end}_lat{lat}_lon{lon}_cap{capacity}.csv', index=True)
    
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

def calculate_net_load_with_pv(load_df, solar_df, load_df_col='Load'):
    """
    Berechnet den tatsächlichen Stromverbrauch unter Berücksichtigung der PV-Anlage.

    Parameters:
        load_df (DataFrame): Stromverbrauch des Haushalts.
        solar_df (DataFrame): Erzeugte Solarenergie.

    Returns:
        DataFrame: Nettoverbrauch (Strombedarf abzüglich PV-Erzeugung).
    """
    load_with_pv_df = load_df.copy()
    load_with_pv_df['Load'] = load_df[load_df_col].sub(solar_df['Electricity'], fill_value=0) #Zieht stundenweise den PV-Ertrag vom Verbrauch ab.
    load_with_pv_df['Load'] = load_with_pv_df['Load'].apply(lambda x: max(x, 0)) # Überschuss = Einspeisung, zählt hier aber nicht als "Last"
    
    print(f"Total Nettoverbrauch (Load with PV):")
    print(load_with_pv_df['Load'].sum())

    return load_with_pv_df


