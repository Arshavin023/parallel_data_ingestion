# Import libraries
from datetime import datetime
import pandas as pd
import os
import time
from pathlib import Path

def main():

    def read_files_into_dictionary(raw_folder_path,processed_folder_path):
        
        # Initialize an empty dictionary to store DataFrames
        dataframes_dict = {}
        # Get a list of all files in the folder
        raw_files = [file for file in os.listdir(raw_folder_path) if file.endswith('.csv')]
        processed_files = [os.path.splitext(file)[0] for file in os.listdir(processed_folder_path) if file.endswith('.csv')]
        
        # Read each Excel file into a DataFrame and add it to the dictionary
        for csv_file in raw_files:
            if (os.path.splitext(csv_file)[0] + '_processed') not in processed_files:
                file_path = os.path.join(raw_folder_path, csv_file)
                try:
                     # Read the CSV file where condition meets
                    filtered_df = pd.read_csv(file_path,header=0)
                    
                    # Create a key from the file name (excluding extension)
                    key = os.path.splitext(csv_file)[0]
                    # Add the DataFrame to the dictionary
                    dataframes_dict[key] = filtered_df
                except pd.errors.EmptyDataError:
                    # Handle the case where the Excel file is empty
                    print(f"Warning: {csv_file} is empty.")
                except Exception as e:
                    # Handle other exceptions (e.g., invalid Excel file)
                    print(f"Error reading {csv_file}: {str(e)}")
            else:
                pass

        return dataframes_dict


    def process_dataframe_in_dictionary(result,processed_folder_path):
        # processed_folder_path = os.path.abspath("C:/Users/uche.nnodim/Desktop/isw_upsl/isw_process_files/test_processed") #destination folder for processed files
        
        try:
            for name, df in result.items():
                date = result[name][['DateTime']].iloc[0,0]
                output_with_D_tran_type = df.groupby('Merchant_Account_Nr').agg(
                    {'Merchant_Receivable':lambda x: (x.count() * 50),
                     'Merchant_Account_Name':lambda x: 'STAMP DUTY POS: ' + date +' '+ str((x.count()+1)),
                     'Transaction_Status': lambda x: 'D',
                     'Tran_ID':lambda x: '',
                     'Trxn_Category': lambda x: ''})

                output_with_D_tran_type.rename(columns={'Merchant_Account_Nr':'account_no',
                                          'Merchant_Receivable':'amount',
                                          'Merchant_Account_Name':'narration',
                                          'Transaction_Status': 'tran_type',
                                          'Tran_ID':'column4',
                                          'Trxn_Category':'pal_account_code'},inplace=True)
                
                output_with_C_tran_type = pd.DataFrame({
                    'Merchant_Account_Nr': ['1022334931'],
                    'amount': [output_with_D_tran_type['amount'].sum()],
                    'narration': ['STAMP DUTY '],
                    'tran_type': ['C'],
                    'column4': [''],
                    'pal_account_code': ['']
                })
                
                final_output = pd.concat([output_with_D_tran_type, output_with_C_tran_type], ignore_index=False)
                final_output = final_output.reset_index()
                final_output.rename({'Merchant_Account_Nr':'account_no'},inplace=True)
                if not os.path.exists(processed_folder_path):
                    os.makedirs(processed_folder_path)
                    final_output.to_csv(f'{processed_folder_path}/{name}_processed.csv',index=False)
                else:
                    final_output.to_csv(f'{processed_folder_path}/{name}_processed.csv',index=False)

        except Exception as e:
            print(f'The following error occurred => {e}')

        return 'processing of all files completed'



    raw_direc = "raw_filepath"
    raw_folder_path = os.path.abspath(raw_direc)
    processed_direc = "processed_filepath"
    processed_folder_path = os.path.abspath(processed_direc)


    # Estimation of how long a 53mb file will take to process
    # Record the start time
    start_time = time.time()

    # Call read file function
    result = read_files_into_dictionary(raw_folder_path,processed_folder_path)
    # Call processing function
    process_dataframe_in_dictionary(result,processed_folder_path)
    print('successfully completed')
    # Record the end time
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    print(f"Time taken: {elapsed_time:.5f} seconds")


if __name__ == "__main__":
    # This block will only be executed if the script is run directly
    main()