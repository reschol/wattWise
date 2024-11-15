# This minimal example on how to retrieve data from the apis
import pandas as pd
import json

from src.utils.renewables_ninja import fetch_solar_data
from src.utils.entsoe_client import fetch_and_save_spot_prices

# Define the API tokens
# Personal renewables.ninja API token
with open(r"D:\Dokumente\Studium\20242025 WS\WattWise\Repo\wattWise\secrets.json") as f:
    secrets = json.load(f)

ninja_token = secrets.get("ninja_token")
entsoe_api_key = secrets.get("entsoe_api_key")

print(ninja_token)

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

    #Local Electricity Consumption Data
    hh_path = r"wattWise\local_input_data\1920 Final Data w. Additional Features HH Hourly Agg.pkl"
    keyword = 'SFH'
    sfh_columns_df = load_and_filter_dataframe(hh_path, keyword, start_date, end_date)
    available_household_loads = sfh_columns_df
    print("Those are available household loads:", available_household_loads)

if __name__ == "__main__":
    main()
