# This minimal example on how to retrieve data from the apis
import random
import pandas as pd
import json

from src.utils.renewables_ninja import fetch_solar_data
from src.utils.entsoe_client import fetch_and_save_spot_prices

from pv_prediction import (
    calculate_net_load_with_pv, 
    load_solar_data_from_csv, 
    get_solar_data_from_api
)

from montecarlo import (
    fill_missing_hours,
    build_weekday_profile_dict,
    generate_random_yearly_profile,
    monte_carlo_simulation_load_profiles,
    calculate_seasonal_factor_per_x,
    apply_seasonal_factors,
    scale_load_profile_to_annual_consumption
)

from customer_input_check import (
    load_pickle_to_dataframe,
    filter_time_range,
    prepare_household_data,
    filter_two_week_data,
    get_random_household_profile,
)

# Define the API tokens
# Personal renewables.ninja API token
with open(r"D:\Dokumente\Studium\20242025 WS\WattWise\Repo\wattWise\secrets.json") as f:
    secrets = json.load(f)

ninja_token = secrets.get("ninja_token")
entsoe_api_key = secrets.get("entsoe_api_key")

#print(ninja_token)

# ninja_token = "" #your renewables.ninja API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
# entsoe_api_key = "" #your entsoe API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
# recommendation: use a JSON file called secrets.json, that is already in the gitignore and should thus be ignored by git


def load_and_filter_dataframe(file_path, keyword, start, end):
    """
    Load a pickle file into a DataFrame and extract columns that contain a specific keyword.

    Parameters:
    - file_path: str, the path to the pickle file.
    - keyword: str, the keyword to filter the columns by.

    Returns:
    - DataFrame containing only the columns that match the keyword.
    """
    # Load the pickle file into a DataFrame
    df = pd.read_pickle(file_path)
    mask = (df.index >= start) & (df.index < end)
    df = df.loc[mask]
    # Extract columns that contain the keyword in their name
    filtered_df = df.filter(like=keyword)
    # turn unit to kWh
    filtered_df = filtered_df/1000

    return filtered_df


def main():
    # ----1. Load the Customer data -----
    hh_path = r"local_input_data\1920 Final Data w. Additional Features HH Hourly Agg.pkl"
    start_2019 = '2019-01-01'
    end_2019 = '2019-12-31'
    start_2020 = '2020-01-01'
    end_2020 = '2020-12-31'
    keyword = 'SFH' # Single Family Households
    exclude = ['SFH34_P_TOT'] # weird profile, not usable

    data_allhouseholds = load_pickle_to_dataframe(hh_path)
    data_2019 = filter_time_range(data_allhouseholds, start_2019, end_2019)
    sfh_2019 = prepare_household_data(data_2019, keyword=keyword, exclude_columns=exclude)
    #data_2020 = filter_time_range(data_allhouseholds, start_2020, end_2020)
    #sfh_2020 = prepare_household_data(data_2020, keyword=keyword, exclude_columns=exclude)
    
    print("Those are the available household loads in 2019:")
    print(sfh_2019.head())
    #--a) Filter the data for a two-week period in 2019
    random_start_date = random.choice(pd.date_range(pd.Timestamp(start_2019), pd.Timestamp(end_2019) - pd.Timedelta(days=14), tz='UTC'))
    random_end_date = random_start_date + pd.Timedelta(days=14)

    two_week_data = filter_two_week_data(sfh_2019, random_start_date, random_end_date)
    print("Filtered two-week data:", two_week_data)
    random_household_two_week = get_random_household_profile(two_week_data)

    print("Random household profile for two weeks:", random_household_two_week)

    #-----2. Load Prediction mit MonteCarlo Simulation
    

    
    #-----3. PV Prediction
    # Lade PV-Erzeugunggsdaten von Renewables.ninja API	
    #Wenn DAtei schon existiert, dann lade sie von /data, wenn nicht, dann lade sie von der API und speichere sie in die Datei
    if csv := 'data/renewables_ninja_data/pv_Karlsruhe_2020.csv':
        try:
            solar_df = load_solar_data_from_csv(csv)
            print("Solar data loaded from CSV.")
        except FileNotFoundError:
            print("File not found, fetching from API.")
            solar_df = get_solar_data_from_api(ninja_token, 50.0, 8.0, '2021-01-01', '2021-12-30', 0.8, 0.1, 90, 180)
    
     


    


    # Netload with PV
    #load_with_pv_df = calculate_net_load_with_pv(solar_df, load_df)








    # Spot market data
    country_code = 'DE_LU'  # 'DE_LU' for 2018 - 2023 and 'DE_AT_LU' for < 2018
    spot_directory = 'data/entsoe_data/normal_hourly'
    start_date = '2019-01-01'
    end_date = '2019-12-31'

    #EntsoE API call
    fetch_and_save_spot_prices(entsoe_api_key, country_code, start_date, end_date, spot_directory)
    
    #Renewables Ninja API call
    solar_data = fetch_solar_data(ninja_token, 50.0, 8.0, '2021-01-01', '2021-12-31',1,0.1,90,180)
    print(solar_data)

    #Local Electricity Consumption Data for Modelling
    hh_path = r"wattWise\local_input_data\1920 Final Data w. Additional Features HH Hourly Agg.pkl"
    keyword = 'SFH'
    sfh_columns_df = load_and_filter_dataframe(hh_path, keyword, start_date, end_date)
    available_household_loads = sfh_columns_df
    print("Those are available household loads:", available_household_loads)

if __name__ == "__main__":
    main()
