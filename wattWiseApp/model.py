import base64
import io
import os
import pandas as pd
"""
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
"""
# Load data from App

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

def run_model_pipeline(lat, lon, cap, loss, tilt, azimuth,
                       annual_consumption, start_date, end_date,
                       forecast_start, model_choice):
    """
    Führt die Modellpipeline aus – Dummy-Implementierung mit Beispielrechnung.

    Args:
        lat (float): Breitengrad
        lon (float): Längengrad
        cap (float): PV-Kapazität in kWp
        loss (float): Systemverluste in Prozent
        tilt (float): Neigungswinkel
        azimuth (float): Azimutwinkel
        annual_consumption (float): Jahresverbrauch in kWh
        start_date (str): Startdatum der Datenbasis
        end_date (str): Enddatum der Datenbasis
        forecast_start (str): Startdatum der Vorhersage
        model_choice (str): Modellwahl ("rf", "lr", "nn")

    Returns:
        dict: Ergebnisse wie simulierte Kosten und Fehlermaß.
    """

    # Beispielberechnungen (Dummy)
    # z. B. Erzeuge "geschätzte" Kosten und Fehlermaß basierend auf Parametern
    base_cost = 300
    pv_bonus = cap * 20  # Annahme: 20 €/kWp "Einsparung"
    loss_penalty = loss * 2

    estimated_cost = base_cost - pv_bonus + loss_penalty
    nmae_dummy = 0.05 + (0.01 if model_choice == "rf" else 0.02)

    return {
        "status": "success",
        "model": model_choice,
        "costs": round(estimated_cost, 2),
        "nmae": round(nmae_dummy, 3)
    }
