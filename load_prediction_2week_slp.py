from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import random
import pickle
import os

weight_offseason_twoweeks = 0.5
weight_offseason_SLP = 0.5

weight_twoweeks = 0.7
weight_SLP = 0.3

def determine_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Autumn'
    
def calculate_prediction_model1(random_household_two_week: pd.DataFrame, start_2019, end_2019, start_2020, end_2020, timestamp_col: str = 'Time', load_col: str = 'Load')-> pd.DataFrame:
    """
    Calculate the prediction for the next year based on two week customer household data.

    Args:
        random_household_two_week (pd.DataFrame): The random household data with two weeks of load data in column 'Load'.
        start_2019 (str): The start date for the training data.
        end_2019 (str): The end date for the training data.
        start_2020 (str): The start date for the test data.
        end_2020 (str): The end date for the test data.
        timestamp_col (str): The name of the timestamp column in the SLP data.
        load_col (str): The name of the load column in the SLP data.
        

    Returns:
        pd.DataFrame: A DataFrame containing the predictions.
    """
    
    #1. Vorbereiten der Customer Daten, Wochenende zuweisen
    df = random_household_two_week.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.set_index(timestamp_col)
    
    df['Weekday'] = df.index.day_name()
    df['Weekend'] = df['Weekday'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)
    df['Hour'] = df.index.hour

    # Durchschnittliche Tagesprofile berechnen aus den Customer Daten
    weekday_data = df[df['Weekend'] == 0]
    weekend_data = df[df['Weekend'] == 1]
    customer_avg_weekday_profile = weekday_data.groupby('Hour')[load_col].mean()
    customer_avg_weekend_profile = weekend_data.groupby('Hour')[load_col].mean()

    # 2. Durchschnittliche Tagesprofile berechnen aus den SLP-Daten vom Vorjahr


    # 3. ModellVorhersage Model1 erstellen
    # Jahreszeitraum vorbereiten
    date_range = pd.date_range(start_2020, end_2020, freq='h')
    pred_df_model1 = pd.DataFrame(index=date_range)
    pred_df_model1 = pred_df_model1[:-1]
    pred_df_model1['Hour'] = pred_df_model1.index.hour
    pred_df_model1['Weekday'] = pred_df_model1.index.day_name()
    pred_df_model1['Weekend'] = pred_df_model1['Weekday'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)
    pred_df_model1['Load'] = 0.0

    for index, row in pred_df_model1.iterrows():
        hour = row['Hour']
        if row['Weekend'] == 0:
            pred_df_model1.at[index, 'Load'] = customer_avg_weekday_profile.get(hour, 0)
        else:
            pred_df_model1.at[index, 'Load'] = customer_avg_weekend_profile.get(hour, 0)

    return pred_df_model1


def calculate_prediction_model2(slp: pd.DataFrame, random_household_two_week: pd.DataFrame, start_2019, end_2019, start_2020, end_2020, timestamp_col: str = 'Time', load_col: str = 'Load', weight_season_twoweek: float = 0.7,
    weight_season_slp: float = 0.3, weight_offseason_twoweek: float = 0.5, weight_offseason_slp: float = 0.5)-> pd.DataFrame:
    """
    Kombiniert Kundenlastprofil (aus 2 Wochen) und SLP zu einer gewichteten Jahresprognose für 2020.

    Args:
        slp (pd.DataFrame): DataFrame mit SLP-Werten ('Load'-Spalte) und Spalte 'Time'.
        random_household_two_week (pd.DataFrame): Zwei Wochen Kundenlastprofil.
        start_2019, end_2019, start_2020, end_2020: Zeitraum für Training/Test.
        timestamp_col (str): Zeitstempelspalte im Kundenprofil
        load_col (str): Lastspalte
        weight_season_twoweek (float): Gewicht des 2-Wochen-Profils in der Hauptsaison.
        weight_season_slp (float): Gewicht des SLP in der Hauptsaison.
        weight_offseason_twoweek (float): Gewicht des 2-Wochen-Profils außerhalb der Saison.
        weight_offseason_slp (float): Gewicht des SLP außerhalb der Saison.

    Returns:
        pd.DataFrame: Prognose-DataFrame mit gewichteter Last, named as 'Load'.
    """

    # Saison bestimmen (erste Datum der zwei Wochen) #TODO


    season = "Winter"  # TODO



    # 2. Durchschnittliche Tagesprofile berechnen aus den SLP-Daten vom Vorjahr
    df_slp = slp.copy()
    df_slp[timestamp_col] = pd.to_datetime(df_slp[timestamp_col])
    df_slp = df_slp.set_index(timestamp_col)
    #print("Spalten in df_slp:", df_slp.columns)
    df_slp['Weekday'] = df_slp.index.day_name()
    df_slp['Weekend'] = df_slp['Weekday'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)
    df_slp['Hour'] = df_slp.index.hour

    # Durchschnittliche Tagesprofile berechnen aus den Customer Daten
    weekday_data = df_slp[df_slp['Weekend'] == 0]
    weekend_data = df_slp[df_slp['Weekend'] == 1]
    customer_avg_weekday_profile_slp = weekday_data.groupby('Hour')[load_col].mean()
    customer_avg_weekend_profile_slp = weekend_data.groupby('Hour')[load_col].mean()

    # Jahrsprofil SLP erstellen
    date_range = pd.date_range(start_2020, end_2020, freq='h')
    pred_df_slp = pd.DataFrame(index=date_range)
    pred_df_slp = pred_df_slp[:-1]
    pred_df_slp['Hour'] = pred_df_slp.index.hour
    pred_df_slp['Weekday'] = pred_df_slp.index.day_name()
    pred_df_slp['Weekend'] = pred_df_slp['Weekday'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)
    pred_df_slp['Load'] = 0.0
    for index, row in pred_df_slp.iterrows():
        hour = row['Hour']
        if row['Weekend'] == 0:
            pred_df_slp.at[index, 'Load'] = customer_avg_weekday_profile_slp.get(hour, 0)
        else:
            pred_df_slp.at[index, 'Load'] = customer_avg_weekend_profile_slp.get(hour, 0)

    # 3. ModellVorhersage Model2 erstellen
    model1 = calculate_prediction_model1(random_household_two_week, start_2019, end_2019, start_2020, end_2020, timestamp_col, load_col)
    model1 = model1.rename(columns={'Load': 'Model1_Load'})
    
    # Rahmen für die Vorhersage erstellen
    model2_pred = model1.copy()
    model2_pred['Season'] = model2_pred.index.map(determine_season)
    model2_pred['SLP_Load'] = pred_df_slp['Load'].values[:len(model2_pred)]  # Stelle sicher, dass Länge passt
    
    def weighted_combination(row):
        if row['Season'] == season:
            return weight_season_twoweek * row['Model1_Load'] + weight_season_slp * row['SLP_Load']
        else:
            return weight_offseason_twoweek * row['Model1_Load'] + weight_offseason_slp * row['SLP_Load']

    model2_pred['Load'] = model2_pred.apply(weighted_combination, axis=1)
    #drop unnecessary columns
    model2_pred = model2_pred.drop(columns=['Model1_Load', 'SLP_Load', 'Season', 'Hour', 'Weekend', 'Weekday'])
    return model2_pred

def scale_load_profile_to_annual_consumption_modelb(df: pd.DataFrame, annual_consumption: float) -> pd.DataFrame:
    """
    Skaliert ein Lastprofil-DataFrame auf den gewünschten Jahresverbrauch.

    Args:
        df (pd.DataFrame): DataFrame mit stündlichem Lastprofil (enthält eine 'Load'-Spalte).
        annual_consumption (float): Ziel-Jahresverbrauch in kWh.

    Returns:
        pd.DataFrame: Skaliertes Lastprofil.
    """
    profile = df.copy()
    total_load = profile['Load'].sum()
    #print(f"Total Load before scaling: {total_load:.2f} kWh")

    if total_load == 0:
        raise ValueError("Gesamtlaufzeit ist 0 – Skalierung nicht möglich.")

    scaling_factor = annual_consumption / total_load
    profile['Load'] *= scaling_factor

    return profile
    


#----------------------------------------Test
from datetime import datetime
start_date = datetime(2020, 1, 1)
date_range = pd.date_range(start_date, periods=24*14, freq='h')
random_data = {
    'Time': date_range,
    'Load': np.random.rand(len(date_range)) * 5  # Zufällige Lastwerte zwischen 0 und 5 kWh
}
random_household_two_week = pd.DataFrame(random_data)

#print("----- Random Household Data:")
#print(random_household_two_week)
# Datumsangaben für das Modell
start_2019 = '2019-01-01'
end_2019 = '2019-12-31'
start_2020 = '2020-01-01'
end_2020 = '2020-12-31'

predictions = calculate_prediction_model1(
    random_household_two_week=random_household_two_week,
    start_2019=start_2019,
    end_2019=end_2019,
    start_2020=start_2020,
    end_2020=end_2020
)
#print("----- Model 1 Predictions:")
#print(predictions)


# Test the second model
date_range2 = pd.date_range(start='2020-01-01 00:00', end='2020-12-30 23:00', freq='h')

slp_data = {
    'Time': date_range2,
    'Load': np.random.rand(len(date_range2)) * 5  # Zufällige Lastwerte zwischen 0 und 5 kWh
}
slp = pd.DataFrame(slp_data)
slp['Time'] = pd.to_datetime(slp['Time'])

#print("----- SLP Data:")
#print(slp)
predictions_model2 = calculate_prediction_model2(
    slp=slp,
    random_household_two_week=random_household_two_week,
    start_2019=start_2019,
    end_2019=end_2019,
    start_2020=start_2020,
    end_2020=end_2020
)
#print("----- Model 2 Predictions:")
#print(predictions_model2)

november = predictions_model2.loc['2020-10-01':'2020-12-30']

plt.figure(figsize=(12, 6))
plt.plot(november.index, november['Load'], label='Model 1 Predictions (Nov 2020)', color='blue')
plt.title('Model 1 Predictions for November 2020')
plt.xlabel('Date')
plt.ylabel('Load (kWh)')
plt.xticks(rotation=45)
plt.grid()
plt.legend()
plt.tight_layout()
#plt.show()
