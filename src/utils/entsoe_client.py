# Credit to Joshua Spreng for the original implementation, fell free to adjust the code to your needs.
import pandas as pd
from entsoe import EntsoePandasClient
from datetime import datetime
import os


def fetch_and_save_spot_prices(api_key, country_code, start_date, end_date, directory):
    """Fetch spot prices from ENTSO-E API and save to a CSV file.
    Args:
        api_key (str): ENTSO-E API key.
        country_code (str): Country code for which to fetch the spot prices (e.g., 'DE' for Germany).
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        output_file (str): Path to the output CSV file.
    """
    client = EntsoePandasClient(api_key=api_key)

    start = pd.Timestamp(start_date, tz='Europe/Brussels')
    end = pd.Timestamp(end_date, tz='Europe/Brussels')

    try:
        spot_prices = client.query_day_ahead_prices(country_code, start=start, end=end)
        spot_prices = spot_prices.tz_convert('Europe/Berlin')  # Convert timezone to CET
        spot_prices = spot_prices.reset_index()
        spot_prices.columns = ['Date (CET)', 'Price (€/MWh)']

        # Format the datetime to the desired format and remove timezone information
        spot_prices['Date (CET)'] = spot_prices['Date (CET)'].dt.strftime('%d.%m.%y %H:%M')

        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Extract the year from the start_date
        year = datetime.strptime(start_date, "%Y-%m-%d").year

        # Create a dynamic file name
        file_name = f'Spot_prices_{country_code}_{year}.csv'
        file_path = os.path.join(directory, file_name)
        spot_prices.to_csv(file_path, index=False, sep=';', decimal=',')
        print(f"Spot prices saved successfully to {file_path}")
    except Exception as e:
        print(f"Error fetching spot prices: {e}")