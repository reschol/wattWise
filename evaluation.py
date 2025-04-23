### ----- Evaluation of the model ----- ### 
#
# This module contains functions to evaluate the performance of the load prediction model.
# It includes functions to calculate the Normalized Mean Absolute Error (NMAE)

# Import necessary libraries
import pandas as pd
from matplotlib import pyplot as plt

#Get actual data from household data 
#TODO fixen
def get_actual_data_from_household_data(household_data: pd.DataFrame, start_date: str, end_date: str, load_col: str = 'Load') -> pd.DataFrame:
    """
    FUNKTION HAT NOCH FEHLER!!!
    Extracts the actual load data from the household data DataFrame.

    Parameters:
        household_data (pd.DataFrame): DataFrame containing household data with a datetime index.
        load_col (str): Name of the column containing load data. Default is 'Load'.
        start_date (str): Start date for the data extraction in 'YYYY-MM-DD' format.
        end_date (str): End date for the data extraction in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: DataFrame with actual load data and datetime index.
    """
    # Ensure the index is in datetime format
    household_data.index = pd.to_datetime(household_data.index)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Extract the actual load data
    actual_load = household_data.loc[start_date:end_date, [load_col]]
    
    
    return actual_load

#Compare Load Forecast to Actual Load with NMAE hourly
def calculate_nmae_load_forecast_to_actual_load_hourly(
    load_forecast: pd.DataFrame,
    actual_load: pd.DataFrame,
    load_forecast_col: str = 'Load',
    actual_load_col: str = 'Load'
) -> float:
    """
    Calculates the Normalized Mean Absolute Error (NMAE) between forecast and actual hourly load.

    Parameters:
        load_forecast (pd.DataFrame): DataFrame with datetime index and forecast values in 'load_forecast_col'.
        actual_load (pd.DataFrame): DataFrame with datetime index and actual values in 'actual_load_col'.
        load_forecast_col (str): Name of the forecast column. Default is 'Load'.
        actual_load_col (str): Name of the actual load column. Default is 'Load'.

    Returns:
        float: NMAE in percent (%), based on sum-normalized absolute error.
    """

    # Extract Series, ensuring they are in the correct format
    forecast_series = load_forecast[load_forecast_col]
    actual_series = actual_load[actual_load_col]

    #print(f"Forecast Series: {forecast_series.head()}")
    #print(f"Actual Series: {actual_series.head()}")

    forecast_series.index = pd.to_datetime(forecast_series.index)
    forecast_series.index = forecast_series.index.tz_convert(None) if forecast_series.index.tz else forecast_series.index
    actual_series.index = pd.to_datetime(actual_series.index)
    actual_series.index = actual_series.index.tz_convert(None) if actual_series.index.tz else actual_series.index
    

    # Ensure both series have the same index
    if not forecast_series.index.equals(actual_series.index):
        raise ValueError("Forecast and actual series must have the same datetime index.")
    # Zeitzonen vereinheitlichen → wir nehmen naive Zeit (ohne +00:00)
    actual_series.index = actual_series.index.tz_convert(None) if actual_series.index.tz else actual_series.index
    forecast_series.index = forecast_series.index.tz_convert(None) if forecast_series.index.tz else forecast_series.index

    
    # Calculate NMAE
    absolute_errors = (forecast_series - actual_series).abs()
    nmae = absolute_errors.sum() / actual_series.abs().sum() * 100  # in %

    print(abs(absolute_errors).sum(), actual_series.abs().sum())
    return nmae

def calculate_nmae_dynmic_price_forecast_actual(
        load_forecast: pd.DataFrame,
        actual_load: pd.DataFrame,
        dynamic_price: pd.DataFrame,
        load_forecast_col: str = 'Load',
        actual_load_col: str = 'Load',
        dynamic_price_col: str = 'DynamicPrice'
):    """
    Calculates the Normalized Mean Absolute Error (NMAE) between forecast and actual load with dynamic price.

    Parameters:
        load_forecast (pd.DataFrame): DataFrame with datetime index and forecast values in 'load_forecast_col'.
        actual_load (pd.DataFrame): DataFrame with datetime index and actual values in 'actual_load_col'.
        dynamic_price (pd.DataFrame): DataFrame with datetime index and dynamic price values in 'dynamic_price_col'.
        load_forecast_col (str): Name of the forecast column. Default is 'Load'.
        actual_load_col (str): Name of the actual load column. Default is 'Load'.
        dynamic_price_col (str): Name of the dynamic price column. Default is 'DynamicPrice'.

    Returns:
        float: NMAE in percent (%), based on sum-normalized absolute error.
    """

    # Extract Series, ensuring they are in the correct format
