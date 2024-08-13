import matplotlib.pyplot as plt
import logging
import os
import pandas as pd
import re
import math
import numpy as np
from memory_profiler import profile
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from src.helper.pdf_generator import *
from src.processing.data_format_converter import *
from src.helper.path_manager import *
from src.helper.file_handler import *
from src.helper.front_end import *

def pre_process_tdms(tdms_parameter_list, state7_time_float):
    print("\n\nPre-proecessing selected TDMS file.")
    # TODO: figure out how to deal with multiple TDMS file
    file_name, tdms_file, sampling_frequency_str = tdms_parameter_list[0]

    data = tdms_file.as_dataframe()
    data.columns = data.columns.str.replace("'", "").str.split('/', n=2).str[2]

    print("Time Aligning Data")
    data["100-HZ-DATA FSW TIME"] -= state7_time_float
    print("Time Alignment Complete")

    if sampling_frequency_str == "1":
        print("1HZ Detected - Filtering out data when Vehicle is OFF")

        pcdu_cntr_rate_threshold = 20
        current_draw_threshold = 1
        test_type_user_input = int(input("\nEnter 1 if S1_ATP, enter 2 if S2_ATP\n"))
        if test_type_user_input == 1:
            pcdu_cntr_rate = "S1 PCDU CNTR RATE"
            current_draw = "S1PS1 CURRENT ACT"
        elif test_type_user_input == 2:
            pcdu_cntr_rate = "S2 PCDU CNTR RATE"
            current_draw = "S2PS1 CURRENT ACT"

        # Original Method of Vehicle OFF filtering
        data = data[(data[pcdu_cntr_rate] > pcdu_cntr_rate_threshold) | (data[current_draw] > current_draw_threshold)]
        print("Vehicle OFF data filtered")

        # Method 2: Find the first index and last index where condition is met. Keep everything in between
        # condition_met_indices = ((data[pcdu_cntr_rate] > pcdu_cntr_rate_threshold) | (data[current_draw] > current_draw_threshold)).to_numpy().nonzero()[0]
        # if condition_met_indices.size > 0:  # Ensure condition was met at least once
        #     start_index = condition_met_indices[0]
        #     end_index = condition_met_indices[-1]
        #
        #     # Slice the DataFrame to keep data between start_index and end_index
        #     data = data.iloc[start_index:end_index + 1]

        print("Vehicle OFF data filtered")

    pre_processed_file_name = file_name + "_pre_processed.parquet"
    pre_processed_file_path = os.path.join(pre_processed_csv_directory, pre_processed_file_name)
    print("converting pre processed data frame into csv")
    data.to_parquet(pre_processed_file_path, index=False)

    return pre_processed_file_path


def filter_data_frame_based_on_time_calculate(dataframe, target_time):
    first_timestamp = dataframe['100-HZ-DATA FSW TIME'].iloc[0]
    index_target_time = None
    for idx, timestamp in enumerate(dataframe['100-HZ-DATA FSW TIME']):
        if timestamp - first_timestamp >= target_time:
            index_target_time = idx
            break

    if index_target_time is not None:
        filtered_data = dataframe.iloc[index_target_time:]

    return filtered_data


def parse_override(override_str):
    if pd.isna(override_str) or override_str == '':
        return []

    if not isinstance(override_str, str):
        QMessageBox.warning(None, "Warning", f"Override value is not a string. Type: {type(override_str)}, Value: {override_str}")
        return []
    actions = []
    try:
        ranges = re.findall(r'\(([^)]+)\)', override_str)
        for r in ranges:
            start, duration = map(float, r.split(','))
            if start < 0 or duration < 0:
                QMessageBox.warning(None, "Warning", f"Invalid range ({start}, {duration}). Skipping.")
                continue
            actions.append((start, duration))
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error parsing override string '{override_str}': {str(e)}")
    return actions


def filter_df_processor(config_df, processed_tdms_df):
    channel_masks = {}
    for index, row in config_df.iterrows():
        # Store variables
        name = row['Channel Name'].strip() if isinstance(row['Channel Name'], str) else row['Channel Name']
        filter_channel_1 = row['Filter Channel 1'].strip() if isinstance(row['Filter Channel 1'], str) else row[
            'Filter Channel 1']
        filter_condition_1 = row['Filter Condition 1']
        filter_channel_2 = row['Filter Channel 2'].strip() if isinstance(row['Filter Channel 2'], str) else row[
            'Filter Channel 2']
        filter_condition_2 = row['Filter Condition 2']
        filter_channel_3 = row['Filter Channel 3'].strip() if isinstance(row['Filter Channel 3'], str) else row[
            'Filter Channel 3']
        filter_condition_3 = row['Filter Condition 3']
        logic_A = row['Logic A']
        logic_B = row['Logic B']
        logic_order = row['Logic Order']
        override_column = row["Manual Override ('16-HZ-DATA FSW TIME', delta time)"]

        # Apply existing filtering logic
        if pd.isna(filter_condition_1):
            pass
        elif pd.isna(logic_order):
            if pd.isna(logic_A):
                processed_tdms_df.loc[processed_tdms_df[filter_channel_1] != filter_condition_1, name] = np.nan
            else:
                condition_A = (processed_tdms_df[filter_channel_1] == filter_condition_1)
                condition_B = (processed_tdms_df[filter_channel_2] == filter_condition_2)
                if logic_A == "&":
                    condition_A &= condition_B
                elif logic_A == "|":
                    condition_A |= condition_B
                processed_tdms_df.loc[~condition_A, name] = np.nan
        else:
            condition_A = (processed_tdms_df[filter_channel_1] == filter_condition_1)
            condition_B = (processed_tdms_df[filter_channel_2] == filter_condition_2)

            if logic_order == "AB":
                if logic_A == "&":
                    condition_A &= condition_B
                elif logic_A == "|":
                    condition_A |= condition_B
                if logic_B == "&":
                    condition_B = condition_A & (processed_tdms_df[filter_channel_3] == filter_condition_3)
                elif logic_B == "|":
                    condition_B = condition_A | (processed_tdms_df[filter_channel_3] == filter_condition_3)
                processed_tdms_df.loc[~condition_B, name] = np.nan
            elif logic_order == "BA":
                if logic_B == "&":
                    condition_B &= (processed_tdms_df[filter_channel_3] == filter_condition_3)
                elif logic_B == "|":
                    condition_B |= (processed_tdms_df[filter_channel_3] == filter_condition_3)
                if logic_A == "&":
                    condition_A = (processed_tdms_df[filter_channel_1] == filter_condition_1) & condition_B
                elif logic_A == "|":
                    condition_A = (processed_tdms_df[filter_channel_1] == filter_condition_1) | condition_B
                processed_tdms_df.loc[~condition_A, name] = np.nan

        name = row['Channel Name'].strip() if isinstance(row['Channel Name'], str) else row['Channel Name']
        print(f"Processing channel: {name}")

        override_column = "Manual Override ('16-HZ-DATA FSW TIME', delta time)"
        if override_column not in row:
            print(f"Warning: '{override_column}' not found in config for channel {name}")
            continue

        override_value = row[override_column]
        override_ranges = parse_override(override_value)
        print(f"Parsed override ranges for {name}: {override_ranges}")

        if override_ranges:
            try:
                mask = pd.Series(False, index=processed_tdms_df.index)
                for start_time, duration in override_ranges:
                    end_time = start_time + duration
                    range_mask = (processed_tdms_df['16-HZ-DATA FSW TIME'] >= start_time) & (processed_tdms_df['16-HZ-DATA FSW TIME'] < end_time)
                    mask |= range_mask
                    print(f"Range ({start_time}, {duration}) affects {range_mask.sum()} rows")
                    print(f"Start time: {start_time}, End time: {end_time}")

                channel_masks[name] = mask
                print(f"Channel {name}: {mask.sum()} values will be set to NaN")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Error creating mask for channel {name}: {str(e)}")

        # Apply all masks at once
        for name, mask in channel_masks.items():
            original_non_nan_count = processed_tdms_df[name].notna().sum()
            processed_tdms_df.loc[mask, name] = np.nan
            new_non_nan_count = processed_tdms_df[name].notna().sum()
            print(f"Channel {name}: {original_non_nan_count - new_non_nan_count} values set to NaN")

    return processed_tdms_df


def exclude_first_n_vectorized(df, column, n):
    # Create a boolean mask for group changes
    group_change = df[column] != df[column].shift()

    # Create group numbers
    group_num = group_change.cumsum()

    # Create a sequence number within each group
    seq_num = group_num.groupby(group_num).cumcount()

    # Create the mask for rows to keep
    mask = seq_num >= n

    return df[mask]

def general_processing(selected_file_directory, processed_tdms_df, config_df, group_channel_bool, filter_points):
    groups = {}
    result = []
    try:
        for index, row in config_df.iterrows():
            channel_nums = []
            channel_names = []

            start_time = time.time()
            # Skip this row and continue to the next one
            if pd.isnull(row.iloc[0]) or not any(char.isalpha() for char in str(row.iloc[0])):
                continue

            section_start = time.time()
            # removal of this line causes: Process finished with exit code -1073740791 (0xC0000409)
            filtered_data = filter_df_processor(config_df, processed_tdms_df)
            section_end = time.time()
            elapsed_time = section_end - section_start
            print(f"Filter_DF: {elapsed_time} seconds")

            section_start = time.time()
            # Store config values
            name = row['Channel Name']
            if isinstance(name, str):  # Check if the value is a string
                name = name.strip()
            filter_channel_1 = row['Filter Channel 1']
            if isinstance(filter_channel_1, str):  # Check if the value is a string
                filter_channel_1 = filter_channel_1.strip()
            min_value_config = row['Min']
            max_value_config = row['Max']
            unit = row['Unit']
            override_column = row["Manual Override ('16-HZ-DATA FSW TIME', delta time)"]

            # check which filter has been applied
            for i in range(1, 4):
                channel_name = row.get(f'Filter Channel {i}')
                if pd.notna(channel_name):
                    channel_nums.append(str(i))
                    channel_names.append(str(channel_name))

            filtered_channels_num = ', '.join(channel_nums) if channel_nums else None
            filtered_channels_name = ', '.join(channel_names) if channel_names else None

            if name not in processed_tdms_df.columns:
                print(f"Channel '{name}' not found in the DataFrame.")
                continue

            # TODO: not a good logic - only relies on filter 1 condition being met
            if isinstance(filter_channel_1, str):  # Check if the value is a string
                filtered_data = exclude_first_n_vectorized(filtered_data, filter_channel_1, filter_points)

            section_end = time.time()
            elapsed_time = section_end - section_start
            print(f"Filter first n data points: {elapsed_time} seconds")

            section_start = time.time()
            # calculation
            min_value_data = filtered_data[name].min()
            max_value_data = filtered_data[name].max()
            avg_data_value = filtered_data[name].mean()
            if pd.notna(min_value_config) and pd.notna(max_value_config):
                min_margin = min_value_data - min_value_config
                max_margin = max_value_config - max_value_data
            else:
                min_margin = np.nan
                max_margin = np.nan

            if pd.isna(min_value_config) and pd.isna(max_value_config):
                status = "NO MIN/MAX RANGE"
            elif pd.isna(min_margin) or pd.isna(max_margin):
                status = "CONDITION NOT MET"
            elif min_margin < 0 or max_margin < 0:
                status = "FAIL"
            else:
                status = "PASS"
            section_end = time.time()
            elapsed_time = section_end - section_start
            print(f"Process Calculation Time: {elapsed_time} seconds")

            section_start = time.time()
            plt.plot(filtered_data['100-HZ-DATA FSW TIME'], filtered_data[name], linewidth = 1)
            plt.ylabel(unit)
            plt.xlabel('Relative Time T = 0 to STATE 7 (Release)')
            plt.grid(True)

            png_name = f"{name} filtered by [{filtered_channels_name}]" if filtered_channels_name is not None else f"{name}"
            name_and_status = (f"{name} - Test Status: {status}") if pd.isna(override_column) else f"{name} - Test Status: {status} - MANUAL OVERRIDE"

            plt.title(name_and_status, fontsize=9)

            # if condition isn't met, show min/max line - reason: better interpretability of data w/ autoscale
            if pd.notna(min_value_config) or pd.notna(max_value_config):
                if min_margin < 0:
                    plt.axhline(y=min_value_config, color='green', linestyle='--', label='Min Range')
                if max_margin < 0:
                    plt.axhline(y=max_value_config, color='red', linestyle='--', label='Max Range')
                if min_margin < 0 or max_margin < 0:
                    plt.legend(loc='center left', bbox_to_anchor=(1.2, 0.5), fontsize=6)
                    plt.subplots_adjust(right=0.7)

            section_end = time.time()
            elapsed_time = section_end - section_start
            print(f"Plot Time: {elapsed_time} seconds")

            section_start = time.time()
            plt.tight_layout()
            result.append((name, round(min_value_data, 2), round(max_value_data, 2), round(avg_data_value, 2), round(min_margin, 2), round(max_margin, 2), status))
            png_directory = os.path.join(selected_file_directory, png_name + ".png")
            plt.savefig(png_directory)
            plt.clf()  # Clear the current figure for the next iteration
            plt.close()
            section_end = time.time()
            elapsed_time = section_end - section_start
            print(f"Result append + PNG Save: {elapsed_time} seconds")

            elapsed_time = section_end - start_time
            print(f"{name} total time: {elapsed_time} seconds\n\n")

    except Exception as e:
        print(f"An error occurred while individual general processing: {str(e)}")
        QMessageBox.critical(None, "Error", f"An error occurred while individual general processing: {str(e)}")

    try:
        if group_channel_bool == "1":
            filtered_data = filter_df_processor(config_df, processed_tdms_df)

            # creates group based on config
            grouped_config = config_df.groupby('Group')

            for group_type, group_data in grouped_config:
                plt.figure()  # This line is moved here
                for index, row in group_data.iterrows():
                    # check which filter has been applied
                    channels = [str(i) for i in range(1, 4) if not pd.isna(row[f'Filter Channel {i}'])]
                    filtered_channels_num = ', '.join(channels) if channels else None

                    channel_names = [str(row[f'Filter Channel {i}']) for i in range(1, 4) if
                                     pd.notna(row[f'Filter Channel {i}'])]
                    filtered_channels_name = ', '.join(channel_names) if channel_names else None

                    unit = row['Unit']
                    name = row['Channel Name']
                    if isinstance(name, str):  # Check if the value is a string
                        name = name.strip()
                    plt.plot(filtered_data['100-HZ-DATA FSW TIME'], filtered_data[name], label=name, linewidth=0.8,
                             alpha=0 if name == 'A2-SDA HAZ 1 BOARD TEMP' else 1)

                png_name = f" Group {group_type} filtered by [{filtered_channels_name}]" if filtered_channels_name is not None else f" Group {group_type}"
                name_and_status = f" Group {group_type}"

                plt.title(name_and_status, fontsize=9)
                plt.ylabel(unit)
                plt.xlabel('Relative Time T = 0 to STATE 7 (Release)')
                plt.grid(True)

                # There will always be a legend for group plot
                plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=6)
                plt.subplots_adjust(right=0.7)
                plt.tight_layout()
                png_directory = os.path.join(selected_file_directory, png_name + ".png")
                plt.savefig(png_directory)
                plt.clf()  # Clear the current figure for the next iteration
                plt.close()

    except Exception as e:
        print(f"An error occurred while group general processing: {str(e)}")
        QMessageBox.critical(None, "Error", f"An error occurred while group general processing: {str(e)}")
    try:
        result_df = pd.DataFrame(result, columns=['Channel Name', 'Min Range', 'Max Range', 'Average', 'Min Margin', 'Max Margin', 'Status'])
        styled_df = result_df.style.applymap(highlight_status, subset=['Status'])
        output_filename_xlsx = os.path.join(selected_file_directory, "CSV_RESULTS.xlsx")
        styled_df.to_excel(output_filename_xlsx, index=False)

        output_filename = os.path.join(selected_file_directory, "PDF_OUTPUT.pdf")
        create_pdf_from_pngs(selected_file_directory, output_filename)
    except Exception as e:
        error_message = f"An error occurred while converting to CSV results and PDF output: {str(e)}"
        QMessageBox.critical(None, "Error", error_message)
