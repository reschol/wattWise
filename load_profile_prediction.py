from matplotlib import pyplot as plt
import pandas as pd
import json

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

def plot_load_profile(df, sfh_column_name):
    """
    Plot the load profile of a single household.

    Parameters:
    - df: DataFrame, the DataFrame containing the load profile data.
    - sfh_column_name: Column name of the single household to plot

    Returns:
    - None.
    """
    # Filter the DataFrame to get the data for the specified household
    household_data = df[sfh_column_name]

    plt.figure(figsize=(10, 6))
    plt.plot(household_data.index, household_data.values, label=sfh_column_name)
    
    plt.xlabel('Time')
    plt.ylabel('Load [kWh]')
    plt.legend()
    plt.grid(True)
    plt.show()


# Model
    def calculate_customer_load_profile(df_database_load_profiles, df_customer_profile_two_weeks, customer_anual_consumption):
        """
        Calculate the load profile of a customer based on the load profiles of similar households.

        Parameters:
        - df_database_load_profiles: DataFrame, the DataFrame containing the load profiles of similar households on an hourly basis.
        - df_customer_profile_two_weeks: DataFrame, the DataFrame containing the load profile of the customer for two weeks on an hourly basis.
        - customer_anual_consumption: float, the annual consumption of the customer.

        Returns:
        - DataFrame containing the hourly load profile of the customer for the whole year.
        """
        #TODO
        
        #Regression over df_database_load_profiles to find seasonal and daily patterns in load profiles. Output: load profiel for the whole year based on database


        #Regression over df_customer_profile_two_weeks to predict the load profile for the whole year. Output: load profile for the whole year based on customer data (two weeks)


        #Compare those two load profiles


        #Apply the regression model to the df_customer_profile_two_weeks to predict the load profile for the whole year


        return df_customer_profile
        



# Testing
    def comparing_real_profile_with_predicted_profile(df_real_profile, df_predicted_profile, df_dynamic_price):
        """
        Compare the real load profile with the predicted load profile and calculate the costs for the customer.

        Parameters:
        - df_real_profile: DataFrame, the DataFrame containing the real load profile of the customer on an hourly basis.
        - df_predicted_profile: DataFrame, the DataFrame containing the predicted load profile of the customer on an hourly basis.
        - df_dynamic_price: DataFrame, the DataFrame containing the dynamic price of electricity on an hourly basis.

        Returns:
        - float, the costs for the customer based on the dynamic price of electricity.
        - bool, True if the predicted load profile is accurate, False otherwise.
        """
        #TODO: Write the code

        #Compare the real load profile with the predicted load profile on an hourly basis. True, if the predicted load profile is accurate, False otherwise.
        #Accurate means error < xxx% #TODO: Define the error.

        #Calculate the costs for the customer based on the dynamic price of electricity. The costs are the sum of the product of the predicted load profile and the dynamic price of electricity on an hourly basis.
        


        return costs












def main():
    start_date = '2019-01-01'
    end_date = '2019-12-31'

    #Local Electricity Consumption Data
    hh_path = r"wattWise\local_input_data\1920 Final Data w. Additional Features HH Hourly Agg.pkl"
    keyword = 'SFH'
    sfh_columns_df = load_and_filter_dataframe(hh_path, keyword, start_date, end_date)
    available_household_loads = sfh_columns_df
    print("Those are available household loads:", available_household_loads)

    #Plot Test Household
    #plot_load_profile(available_household_loads, 'SFH3_P_TOT')

if __name__ == "__main__":
    main()


