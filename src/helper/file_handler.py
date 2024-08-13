import threading
import nptdms
import logging
import json


from src.helper.path_manager import *
from src.helper.front_end import *

def load_csv_file_name():
    csv_files_ordered_list = [file for file in os.listdir(pre_processed_csv_directory) if file.endswith(".csv")]
    # Print the list of CSV files in the selected directory
    print("\n\nList of CSV files in the selected directory:\n\n")
    for index, file in enumerate(csv_files_ordered_list, start=1):
        print(f"{index}.{file}")
    # Get user input for selecting a CSV file
    user_input = input("\nEnter the number of the CSV file you want to load: ")
    selected_number = int(user_input)
    if selected_number < 1 or selected_number > len(csv_files_ordered_list):
        print("Invalid input. Please enter a valid number.")
    else:
        selected_file = csv_files_ordered_list[selected_number - 1]  # Adjust for 0-based indexing
        selected_file_path = os.path.join(pre_processed_csv_directory, selected_file)
        print(selected_file_path)
    return selected_file_path


def load_tdms() -> list:
    """
    :return:
    list: A list of tuples, each containing the file name, TDMSFile object, and sampling frequency.
    """
    print(r"Enter the file location of tdms file")
    print(r"ex - O:\Briggs\Test Stand 2\Stage 2\1228 FLTA004 Stage Two Acceptance\3.0-Hot_Fire_Data_Files\09-08-23\2023-09-08-TST_0030_HF_03)")
    file_location, file_base_name = file_location_user_input()
    tdms_files_ordered_list = [file for file in os.listdir(file_location) if file.endswith(".tdms")]
    print("\n\nList of TDMS file in the selected directory:\n\n")
    for index, file in enumerate(tdms_files_ordered_list, start=0):
        print(f"{index}.{file}")

    user_input = input("\nEnter the list number of the TDMS files you want to load (e.g., '1 3 5' or '0 22'): ")
    selected_numbers = [int(num) for num in user_input.split()]
    selected_files = [tdms_files_ordered_list[num] for num in selected_numbers]

    sampling_frequency = input("\nEnter the sampling frequency of the tdms file\n")

    loaded_files = []
    threads = []

    for file_index, file in enumerate(selected_files, start=1):
        file_path = os.path.join(file_location, file)

        # visual fake loading bar
        loading_bar_thread = threading.Thread(target=update_loading_bar)
        loading_bar_thread.start()
        threads.append(loading_bar_thread)

        tdms_file = nptdms.TdmsFile.read(file_path)
        loaded_files.append((file, tdms_file, sampling_frequency))
    for thread in threads:
        thread.join()

    print("\nAll selected files loaded successfully!")
    return loaded_files

def parse_for_state7_time_txt() -> int:
    bool_state7_txt = input("\nIs there a TM Events File? Enter 0 if No, 1 if Yes\n")
    if bool_state7_txt == "0":
        #state7_time = float(input("enter time of state 7:\n"))
        state7_time = 30233
        return state7_time
    else:
        print("\nEnter the file location of TM Events txt file\n")
        print(r"ex - O:\Briggs\Test Stand 2\Stage 2\1228 FLTA004 Stage Two Acceptance\3.0-Hot_Fire_Data_Files\09-08-23\2023-09-08-TST_0030_HF_03)")

    file_location, _ = file_location_user_input()
    txt_files_ordered_list = [file for file in os.listdir(file_location) if file.endswith(".txt")]

    print("\n\nList of text file in the selected directory:\n\n")

    for index, file in enumerate(txt_files_ordered_list, start=0):
        print(f"{index}.{file}")
    selected_number = int(input("\nEnter the list number of the TM Events text file:"))
    selected_file = txt_files_ordered_list[selected_number]
    file_path = os.path.join(file_location, selected_file)

    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Iterate through the lines to find the desired information
        for line in lines:
            if 'State Machine State Change (1)' in line and 'ID 7' in line:
                # Extract the time from the line
                state7_time = float(line.split()[1])
                print(f'Time when State Machine State Change (1) ID 7 occurred: {state7_time}')
                return state7_time
    return None


def find_png_files(directory):
    png_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.png'):
                png_files.append(os.path.join(root, file))
    return png_files