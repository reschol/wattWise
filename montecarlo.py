import numpy as np
import pandas as pd
import random

# ---- 1. Load Data  ----
# Standard-Lastprofil für 2019 (stündlich)
file_path = r"D:\Dokumente\Studium\20242025 WS\WattWise\Repo\wattWise\data\slp\GGV_SLP_1000_MWh_2019_01.xlsx"
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

#Prepare DataFrame
df_standard_load_profile_2019.drop(columns=['Messwert-Nr.','MP von', 'MP bis'], inplace=True)

#Fasse Zeitstempel pro Stunde zusammen und summiere H00 [kW] in neuer df
df_standard_load_profile_2019['Time'] = df_standard_load_profile_2019['Zeitstempel von'].dt.floor('h')

df_agg = df_standard_load_profile_2019.groupby('Time').agg({'H00 [kW]': 'sum'}).reset_index()
df_agg['H00 [kWh]'] = df_agg['H00 [kW]'] / 4 

df_standard_load_profile_2019 = fill_missing_hours(df=df_agg, time_col='Time', value_cols=['H00 [kWh]'],
    year=2019,
    fill_value=0 # oder np.nan
)
#add 'Wochentag'
df_standard_load_profile_2019['Weekday'] = df_standard_load_profile_2019['Time'].dt.day_name()

#add Arbeitstag oder Wochenende als neue Spalte
df_standard_load_profile_2019['Weekend'] = df_standard_load_profile_2019['Weekday'].apply(lambda x: 1 if x in ['Saturday', 'Sunday'] else 0)

#add Hour and save as int
df_standard_load_profile_2019['Hour'] = df_standard_load_profile_2019['Time'].dt.time
df_standard_load_profile_2019['Hour'] = df_standard_load_profile_2019['Hour'].apply(lambda x: x.hour)

#Normalizing the values to a "average household" with 3000 kWh  
df_standard_load_profile_2019['Normalized Load'] = df_standard_load_profile_2019['H00 [kWh]'] /df_standard_load_profile_2019['H00 [kWh]'].sum()*3000

#Save an seaonality index for each hour on a annual mean of 1.0
df_standard_load_profile_2019['Seasonal Factor'] = df_standard_load_profile_2019['Normalized Load'] / df_standard_load_profile_2019['Normalized Load'].mean()


# ------ Zwei Wochen Kundenverbrauch für 2020 (stündlich) -- hier ggf. Input ändern #TODO
#--a) Input #TODOsiehe customer_input_check.py

#--b) Funktion, die aus einem DataFrame mit Zeitstempeln und Lastwerten Dictionary erzeugt, das Wochentage als Keys und Listen von Tagesprofilen (DataFrames mit 24 Stunden) als Values enthält.
def build_weekday_profile_dict(df: pd.DataFrame, timestamp_col: str = 'Time', load_col: str = 'Load') -> dict:
    """
    Baut ein Dictionary mit Wochentags-Keys (Monday–Sunday) und Listen von Tagesprofilen (DataFrames mit 24 Stunden) als Values.

    Args:
        df (pd.DataFrame): DataFrame mit Zeitreihe über mehrere Tage (14 Tage). Muss Spalten für Zeitstempel und Last enthalten.
        timestamp_col (str): Name der Zeitstempelspalte. Default: 'Time'.
        load_col (str): Name der Lastspalte. Default: 'Load'.

    Returns:
        dict: Dictionary mit Wochentagen als Keys und Listen von Tages-DataFrames (je 24 Stunden) als Values.
    """

    # Stelle sicher, dass Time im richtigen Format ist
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df['Weekday'] = df[timestamp_col].dt.day_name()
    df['Date'] = df[timestamp_col].dt.date

    # Nach Tag gruppieren
    grouped_by_day = df.groupby('Date')

    # Dictionary zum Befüllen
    weekday_profiles = {}

    for date, group in grouped_by_day:
        if len(group) != 24:
            continue  # überspringe unvollständige Tage

        weekday = group['Weekday'].iloc[0]

        if weekday not in weekday_profiles:
            weekday_profiles[weekday] = []

        # Nur die Lastwerte als DataFrame (Index 0–23)
        daily_profile = group[[load_col]].reset_index(drop=True)
        weekday_profiles[weekday].append(daily_profile)

    return weekday_profiles

#------- 2.  Jahreslastprofil erstellen-------------------
#--a) Pro Wochentag wähle ein Lastprofi aus two week data zufällig aus

def generate_random_yearly_profile(weekday_dfs_with_load: dict, year: int) -> pd.DataFrame:
    """
    Erstellt ein zufälliges Jahreslastprofil, indem für jeden Tag im Jahr ein zufälliges Tagesprofil
    aus dem passenden Wochentags-Pool aus `weekday_dfs_with_load` gezogen wird.

    Args:
        weekday_dfs_with_load (dict): Dictionary mit Wochentagsnamen als Keys und Listen von Tagesprofilen (DataFrames mit 24 Stunden) als Values.
        year (int): Jahr, für das das Lastprofil erzeugt werden soll.

    Returns:
        pd.DataFrame: Zeitreihe mit stündlichem Lastprofil für das gesamte Jahr.
    """

    # Erstelle Zeitindex für das ganze Jahr (stündlich)
    start = pd.Timestamp(f"{year}-01-01 00:00")
    end = pd.Timestamp(f"{year}-12-31 23:00")
    full_index = pd.date_range(start, end, freq='h')

    # Leerer DataFrame für das Jahresprofil
    full_year_profile = pd.DataFrame(index=full_index)
    full_year_profile['Load'] = 0.0

    # Gruppiere den Index nach Datum
    grouped = full_year_profile.groupby(full_year_profile.index.date)

    for day, group in grouped:
        weekday_name = pd.Timestamp(day).day_name() #Wochentag des Tages

        # Ziehe zufälliges Tagesprofil aus passendem Pool
        profile_list = weekday_dfs_with_load.get(weekday_name, [])
        
        chosen_profile = random.choice(profile_list)

        # Trage die Lastwerte in die passenden Stunden ein
        full_year_profile.loc[group.index, 'Load'] = chosen_profile['Load'].values

    return full_year_profile
    
#--b) Monte Carlo Simulation über mehrere Lastprofile
#Dafür generate_random_yearly_profile über das selbe Jahr aufrufen
def monte_carlo_simulation_load_profiles(weekday_dfs_with_load: dict, year: int, n_simulations: int) -> list:
    """
    Führt eine Monte-Carlo-Simulation durch, bei der mehrere zufällige Jahreslastprofile generiert werden.

    Args:
        weekday_dfs_with_load (dict): Dictionary mit Wochentagsnamen als Keys und Listen von Tagesprofilen (DataFrames mit 24 Stunden) als Values.
        year (int): Jahr, für das die Profile generiert werden.
        n_simulations (int): Anzahl der gewünschten Simulationen.

    Returns:
        list: Liste mit DataFrames, jeweils ein vollständiges Jahreslastprofil.
    """
    simulations = []

    for i in range(n_simulations):
        simulated_profile = generate_random_yearly_profile(weekday_dfs_with_load, year)
        simulations.append(simulated_profile)

    return simulations

#--c) Seasonality Index
# Jedem MOnat/Kalenderweoche aus SLP ein Seasonality Factor hinzufügen
def calculate_seasonal_factor_per_x(df_slp: pd.DataFrame, x: str = "Month"):
    """
    Berechnet den saisonalen Faktor für jeden Monat oder Tag im DataFrame.

    Args:
        df_slp (DataFrame): DataFrame Standardlastprofil mit einer Zeitspalte und einer Spalte für den saisonalen Faktor.
        x (str): 'Month' oder 'Day', 'Calendar Week' um den saisonalen Faktor zu berechnen.

    Returns:
        DataFrame mit dem saisonalen Faktor.
    """
    if x == "Month":
        seasonal_factor = df_slp.groupby(df_slp['Time'].dt.month)['Seasonal Factor'].mean().reset_index()
        seasonal_factor.rename(columns={'Seasonal Factor': 'Seasonal Factor'}, inplace=True)
    elif x == "Day":
        seasonal_factor = df_slp.groupby(df_slp['Time'].dt.day)['Seasonal Factor'].mean().reset_index()
        seasonal_factor.rename(columns={'Seasonal Factor': 'Seasonal Factor'}, inplace=True)
    elif x == "Calendar Week":
        seasonal_factor = df_slp.groupby(df_slp['Time'].dt.isocalendar().week)['Seasonal Factor'].mean().reset_index()
        seasonal_factor.rename(columns={'Seasonal Factor': 'Seasonal Factor'}, inplace=True)
    else:
        raise ValueError("x must be either 'Month' or 'Day' or 'Calendar Week'.")

    return seasonal_factor

# Checken, aus welcher Jahreszeit two week data ist. #TODO weil das natürlich Auswirkungen auf miteinberechnete Seasonality hat? Oder wird das mathematisch durch Normalisierung am Ende egal betrachtet?


#Jahreslastprofile mit Seasonality Factor multiplizieren
def apply_seasonal_factors(simulations: list, seasonal_factors: pd.DataFrame, by: str = "Month") -> list:
    """
    Multipliziert jeden Load-Wert in den Simulationen mit dem passenden saisonalen Faktor
    entweder nach Monat oder nach Kalenderwoche.

    Args:
        simulations (list): Liste von DataFrames mit datetime-index und 'Load'-Spalte.
        seasonal_factors (pd.DataFrame): DataFrame mit Spalten 'Month' oder 'Calendar Week' und 'Seasonal Factor'.
        by (str): 'Month' oder 'Calendar Week', je nachdem wie die Faktoren aufgebaut sind.

    Returns:
        list: Liste angepasster DataFrames mit modifizierten 'Load'-Werten.
    """
    if by not in ['Month', 'Calendar Week']:
        raise ValueError("Parameter 'by' muss 'Month' oder 'Calendar Week' sein.")

    adjusted_simulations = []

    for df in simulations:
        df = df.copy()
        df['Time'] = pd.to_datetime(df.index)
        if by == 'Month':
            df['TimeKey'] = df.index.month
            merge_col = 'Time'
        elif by == 'Calendar Week':
            df['TimeKey'] = df.index.isocalendar().week
            merge_col = 'Time'

        # Merge mit saisonalen Faktoren
        df = df.merge(seasonal_factors, how='left', left_on='TimeKey', right_on=merge_col)
        df['Load'] = df['Load'] * df['Seasonal Factor']

        # Aufräumen
        df.drop(columns=['Time_y', 'TimeKey', 'Seasonal Factor'], inplace=True)
        df['Time'] = df['Time_x']
        df.drop(columns=['Time_x'], inplace=True)
        df.set_index('Time', inplace=True)
        adjusted_simulations.append(df)

    return adjusted_simulations

#--d) Normalisieren auf den Jahresverbrauch
def scale_load_profile_to_annual_consumption(df: list, annual_consumption: float) -> pd.DataFrame:
    """
    Skaliert das Lastprofil auf den gewünschten Jahresverbrauch.

    Args:
        df (list): Liste von DataFrames mit stündlichem Lastprofil.
        annual_consumption (float): Vergangener Jahresverbrauch in kWh.

    Returns:
        list: Liste von DataFrames mit skaliertem Lastprofil.
    """
    scaled_profiles = []

    for profile in df:
        profile = profile.copy()
        total_load = profile['Load'].sum()
        print(f"Total Load: {total_load} kWh")
        scaling_factor = annual_consumption / total_load
        profile['Load'] *= scaling_factor
        scaled_profiles.append(profile)

    return scaled_profiles
