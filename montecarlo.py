import numpy as np
import pandas as pd
import random
import pickle
import os

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


# -------------3. Dynamische Preise integrieren------------------
#--a) Dynamische Preise laden (stündlich)
def load_spot_market_prices(
    start_date: str,
    end_date: str,
    country_code: str = 'DE_LU',
    data_dir: str = 'data/entsoe_data/normal_hourly',
    index_new_df_col: str = 'Time',
) -> pd.DataFrame:
    """
    Lädt und konvertiert Spotmarktpreise (€/MWh → ct/kWh) für einen gegebenen Zeitraum.

    Args:
        start_date (str): Startdatum im Format 'YYYY-MM-DD'.
        end_date (str): Enddatum im Format 'YYYY-MM-DD'.
        country_code (str): Ländercode für die Datei (z. B. 'DE_LU'). 'DE_LU' for 2018 - 2023 and 'DE_AT_LU' for < 2018
        data_dir (str): Pfad zum Speicherort der CSV-Dateien.
        show_summary (bool): Gibt den Durchschnittspreis aus, wenn True.
        index_new_df_col (str): Name der neuen Indexspalte. Default: 'Time'. Indexspaltenname der data_dir Datei: 'Date (CET)'
    Returns:
        pd.DataFrame: Gefilterte Spotmarktdaten mit datetime-index und Spalte 'Price ct/KWH'.
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Ermittle alle Jahre im Zeitraum
    years = list(range(start.year, end.year + 1))
    dfs = []

    for year in years:
        file_path = f"{data_dir}/Spot_prices_{country_code}_{year}.csv"
        try:
            df = pd.read_csv(
                file_path,
                delimiter=';',
                decimal=',',
                parse_dates=['Date (CET)'],
                dayfirst=True
            )
            df['Price ct/KWH'] = df['Price (€/MWh)'] / 1000 * 100
            df[index_new_df_col] = df['Date (CET)']
            df.drop(columns=['Date (CET)'], inplace=True)
            df.set_index(index_new_df_col, inplace=True)
            dfs.append(df[['Price ct/KWH']])
        except FileNotFoundError:
            print(f"Datei nicht gefunden: {file_path}")

    if not dfs:
        print("Keine Daten geladen.")
        return pd.DataFrame()

    # Alle Jahre zusammenfügen
    full_df = pd.concat(dfs)

    # Nach Zeitraum filtern
    full_df = full_df.loc[start:end]

    return full_df


def calculate_dynamic_price_with_fees(
    spot_prices: pd.DataFrame,
    start_date: str,
    end_date: str,
    price_col: str = 'Price ct/KWH',
    consumption_dependent_fixed_costs: float = 19.71,  # ct/kWh
) -> pd.DataFrame:
    """
    Berechnet den dynamischen Strompreis (€/kWh) für einen gegebenen Zeitraum
    auf Basis von Spotmarktpreisen und zusätzlichen Kosten.

    Args:
        spot_prices (pd.DataFrame): Spotpreise mit Zeitindex und Spalte in ct/kWh.
        start_date (str): Startdatum im Format 'YYYY-MM-DD'.
        end_date (str): Enddatum im Format 'YYYY-MM-DD'.
        price_col (str): Name der Preisspalte in ct/kWh.
        consumption_dependent_fixed_costs (float): Aufschlag in ct/kWh.
        base_price_per_month (float): Grundpreis in €/Monat.

    Returns:
        pd.DataFrame: DataFrame mit Spalte 'Dynamic Price €/kWh' für den Zeitraum.
    """

    # Sicherstellen, dass der Index datetime ist
    spot_prices = spot_prices.copy()
    spot_prices.index = pd.to_datetime(spot_prices.index)

    # Zeitraum filtern
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    df_period = spot_prices.loc[start:end]

    if df_period.empty:
        print(f"Keine Spotpreise im Zeitraum {start_date} bis {end_date} gefunden.")
        return pd.DataFrame()

    # Umrechnung ct/kWh → €/kWh mit Verbrauchsaufschlag
    df_period = df_period.copy()
    df_period['Dynamic Price €/kWh'] = (df_period[price_col] + consumption_dependent_fixed_costs) / 100

    return df_period[['Dynamic Price €/kWh']]

def get_fixed_price_per_kwh(
    year: int,
    csv_path: str = 'data/electricity_prices_yearly/electricity_prices_yearly2014_2024.csv',
    price_col: str = 'Summe'
) -> float:
    """
    Extrahiert den festen Strompreis (€/kWh) für ein bestimmtes Jahr aus einer CSV-Datei.

    Args:
        year (int): Zieljahr (z. B. 2020)
        csv_path (str): Pfad zur CSV-Datei mit jährlichen Preisen (in ct/kWh)
        price_col (str): Spaltenname mit Gesamtpreis (in ct/kWh)

    Returns:
        float: Fixpreis in €/kWh
    """
    try:
        df = pd.read_csv(csv_path, delimiter=',', decimal='.', parse_dates=['Year'])
        df['Year'] = df['Year'].dt.year
    except Exception as e:
        print(f"Fehler beim Laden der Datei: {e}")
        return float('nan')

    if year not in df['Year'].values:
        print(f"Kein Eintrag für das Jahr {year} in der Datei.")
        return float('nan')

    # Preis in €/kWh umrechnen (aus ct/kWh)
    fixed_price_ct = df.loc[df['Year'] == year, price_col].values[0]
    fixed_price_eur = fixed_price_ct / 100

    return fixed_price_eur


def calculate_annual_dynamic_costs(df_load_profile, df_dynamic_price, dynamic_base_price_per_month = 15.73, load_col='Load', price_col='Dynamic Price €/kWh'):
    """
    Berechnet die jährlichen Kosten basierend auf dem Lastprofil und den dynamischen Preisen.
   

    Args:
        df_load_profile (pd.DataFrame): DataFrame mit Lastprofil und Zeitindex.
        df_dynamic_price (pd.DataFrame): DataFrame mit dynamischen Preisen und Zeitindex.
        dynamic_base_price_per_month (float): Monatlicher Grundpreis in €/Monat. Default: 15.73 # € / Monat #TODO 2024 value Tibber - Example value, replace with actual value


        load_col (str): Name der Lastspalte. Default: 'Load'.
        price_col (str): Name der Preisspalte. Default: 'Dynamic Price €/kWh'.

    Returns:
        float: Jährliche Kosten in Euro.
    """
    # Sicherstellen, dass die Indizes übereinstimmen
    df_load_profile.index = pd.to_datetime(df_load_profile.index)
    if df_load_profile.index.tz is not None:
        df_load_profile.index = df_load_profile.index.tz_convert(None)

    df_dynamic_price.index = pd.to_datetime(df_dynamic_price.index)
    if df_dynamic_price.index.tz is not None:
        df_dynamic_price.index = df_dynamic_price.index.tz_convert(None)

    #if not df_load_profile.index.equals(df_dynamic_price.index):
        #print("Zeitachsen stimmen nicht überein!")
        #print(f"- df_load_profile:type = {type(df_load_profile.index)}, dtype = {df_load_profile.index.dtype}, tz = {df_load_profile.index.tz}")
        #print(f"- df_dynamic_price:type = {type(df_dynamic_price.index)}, dtype = {df_dynamic_price.index.dtype}, tz = {df_dynamic_price.index.tz}")
    #else:
    #    print("Indices sind identisch!")

    # Berechnung der jährlichen Kosten
    annual_costs = ((df_load_profile[load_col] * df_dynamic_price[price_col]).sum(axis=0)) + dynamic_base_price_per_month*12
    return annual_costs

    
def calculate_annual_static_costs(df_load_profile, static_price_per_kwh, load_col='Load', price_col='Static Price €/kWh'):
    """
    Berechnet die jährlichen Kosten basierend auf dem Lastprofil und den statischen Preisen.
    
    Args:
        df_load_profile (pd.DataFrame): DataFrame mit Lastprofil und Zeitindex.
        static_price_per_kwh (float): Statischer Preis in €/kWh.
        load_col (str): Name der Lastspalte. Default: 'Load'.
        price_col (str): Name der Preisspalte. Default: 'Static Price €/kWh'.

    Returns:
        float: Jährliche Kosten in Euro.
    """
    
    annual_costs = (df_load_profile[load_col].sum(axis=0) * static_price_per_kwh[price_col])

    return annual_costs

def load_or_run_simulation(household_col, profile_dict, year, n_simulations):
    """
    Lädt gespeicherte Monte-Carlo-Simulationen für einen Haushalt aus einem Cache-Ordner,
    oder führt die Simulation neu aus, wenn noch kein Ergebnis vorhanden ist.

    Args:
        household_col (str): Der Name der Haushaltsspalte, z. B. 'SFH4_P_TOT'
        profile_dict (dict): Weekday-Profil des Haushalts (Ergebnis von build_weekday_profile_dict)
        year (int): Jahr der Simulation (z. B. 2020)
        n_simulations (int): Anzahl der zu generierenden Simulationsläufe

    Returns:
        list of pd.DataFrame: Liste mit simulierten Lastprofilen (z. B. 100 DataFrames)
    """

    # Pfad zur Cache-Datei definieren (z. B. simulations_cache/SFH4_P_TOT_simulations.pkl)
    cache_path = f"simulations_cache/{household_col}_simulations.pkl"
    
    # Prüfen, ob Cache-Datei bereits existiert
    if os.path.exists(cache_path):
        # Falls ja: Lade die Simulationen aus der Datei
        with open(cache_path, "rb") as f:
            print(f"→ Loaded cached simulations for {household_col}")
            return pickle.load(f)
    else:
        # Falls nein: Starte neue Monte-Carlo-Simulation
        print(f"→ Running new simulations for {household_col} ...")
        simulations = monte_carlo_simulation_load_profiles(profile_dict, year, n_simulations)

        # Speichere die Simulationen für späteres Wiederverwenden
        with open(cache_path, "wb") as f:
            pickle.dump(simulations, f)
        
        return simulations