# This minimal example on how to retrieve data from the apis

from src.utils.renewables_ninja import fetch_solar_data
from src.utils.entsoe_client import fetch_and_save_spot_prices

# Define the API tokens
# Personal renewables.ninja API token
ninja_token = "" #your renewables.ninja API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
entsoe_api_key = "" #your entsoe API token (to be stored in a JSON which is the gitignore and thus never comitted/pushed)
# recommendation: use a JSON file called secrets.json, that is already in the gitignore and should thus be ignored by git

def main():
    # Spot market data
    country_code = 'DE_LU'  # 'DE_LU' for 2018 - 2023 and 'DE_AT_LU' for < 2018
    spot_directory = 'data/entsoe_data/normal_hourly'
    start_date = '2021-01-01'
    end_date = '2021-12-31'
    fetch_and_save_spot_prices(entsoe_api_key, country_code, start_date, end_date, spot_directory)
    solar_data = fetch_solar_data(ninja_token, 50.0, 8.0, '2021-01-01', '2021-12-31',1,0.1,90,180)
    print(solar_data)


if __name__ == "__main__":
    main()
