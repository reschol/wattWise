import pandas as pd


#------ 1. Load pickle into dataframe ------
def load_pickle_to_dataframe(path: str) -> pd.DataFrame:
    """
    Lädt eine Pickle-Datei als DataFrame und fügt eine 'Time'-Spalte aus dem Index hinzu.
    
    Args:
        path (str): Pfad zur Pickle-Datei.
        
    Returns:
        DataFrame: Geladene Daten mit 'Time'-Spalte.
    """
    df = pd.read_pickle(path)
    df['Time'] = df.index
    return df


def filter_time_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Filtert einen DataFrame auf Basis eines Datumsbereichs.

    Args:
        df (pd.DataFrame): Zeitreihen-DataFrame mit datetime-Index.
        start_date (str): Startdatum (inklusiv).
        end_date (str): Enddatum (exklusiv).

    Returns:
        DataFrame: Gefilterter DataFrame im angegebenen Zeitraum.
    """
    mask = (df.index >= start_date) & (df.index < end_date)
    return df.loc[mask]

def prepare_household_data(df: pd.DataFrame, keyword: str, exclude_columns: list = None) -> pd.DataFrame:
    """
    Filtert nach Spalten mit einem bestimmten Keyword und entfernt optional unerwünschte Spalten.
    Rechnet die Einheit in kWh um (falls nötig).

    Args:
        df (pd.DataFrame): Zeitreihen-DataFrame.
        keyword (str): Schlagwort zur Filterung der Haushalts-Spalten (z. B. 'SFH').
        exclude_columns (list): Liste von Spaltennamen, die entfernt werden sollen.

    Returns:
        DataFrame: Gefilterter und umgerechneter DataFrame.
    """
    filtered_df = df.filter(like=keyword)
    
    if exclude_columns:
        filtered_df = filtered_df.drop(columns=exclude_columns, errors='ignore')
    
    # Umrechnung in kWh (angenommen: Originaleinheit ist Wh)
    filtered_df = filtered_df / 1000

    return filtered_df

#------ 2. 2019 ------



#------- 4. Two Week Data 2019 ------
def filter_two_week_data(df_houshold_load_fullyear_model: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """
    Filter the DataFrame to include only the data between the specified start and end dates.
    
    Args:
        df_houshold_load_fullyear_model: DataFrame containing household load data from all households for the entire year. We now only chose 2 weeks. 
        start_date: Start date for filtering (inclusive)
        end_date: End date for filtering (inclusive)

    Returns: 
        two-week DataFrame from all households.
    """

    df = df_houshold_load_fullyear_model.loc[start_date:end_date]
    #DElete last row (00:00)
    df = df[:-1]
    return df

#-------- 5. Give back one random household two week profile ------
def get_random_household_profile(df: pd.DataFrame) -> pd.Series:
    """
    Get a random household profile from the DataFrame.
    
    Args:
        df: two-week DataFrame from all households..

    Returns:
        Series containing the load profile of a random household.
    """
    # Select a random column (household)
    random_household = df.sample(axis=1, n=1).iloc[:, 0]
    return random_household
