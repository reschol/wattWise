# Credit to Joshua Spreng for the original implementation, fell free to adjust the code to your needs.

import requests
import pandas as pd
import json


def fetch_solar_data(token, lat, lon, date_from, date_to, capacity, system_loss, tilt, azim, dataset='merra2', tracking=0):
    api_base = 'https://www.renewables.ninja/api/'
    s = requests.Session()
    s.headers.update({'Authorization': f'Token {token}'})

    url = api_base + 'data/pv'
    args = {
        'lat': lat,
        'lon': lon,
        'date_from': date_from,
        'date_to': date_to,
        'dataset': dataset,
        'capacity': capacity,
        'system_loss': system_loss,
        'tracking': tracking,
        'tilt': tilt,
        'azim': azim,
        'format': 'json'
    }

    try:
        response = s.get(url, params=args)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        parsed_response = json.loads(response.text)

        if 'data' in parsed_response:
            timestamps = []
            electricity = []
            for timestamp, data in parsed_response['data'].items():
                timestamps.append(pd.to_datetime(int(timestamp), unit='ms'))
                electricity.append(data['electricity'])

            data = pd.DataFrame({'Time': timestamps, 'Electricity': electricity})
            data.set_index('Time', inplace=True)
            # data['Time'] = pd.to_datetime(data['Time'], format='%d.%m.%y %H:%M')

            return data, parsed_response.get('metadata', {})

        else:
            print('No data found in the response')
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch solar data: {str(e)}")
        return None, None


