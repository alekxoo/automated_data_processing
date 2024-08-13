import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.
        return sys._MEIPASS
    else:
        # Otherwise, we're running in a normal Python environment
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the base path
base_path = get_base_path()

# Construct paths to other directories relative to the base path
src_directory = os.path.join(base_path, 'src')
config_directory = os.path.join(src_directory, 'config')
project_directory = base_path
pre_processed_csv_directory = os.path.join(project_directory, 'data', 'pre_processed_csv')
data_directory = os.path.join(project_directory, 'data')

LS_data_directory = os.path.join(project_directory, 'data', 'LS_data')
MS_data_directory = os.path.join(project_directory, 'data', 'MS_data')
sensor_check_directory = os.path.join(project_directory, 'data', 'sensor_check')
thermal_check_directory = os.path.join(project_directory, 'data', 'thermal_check')
valve_check_directory = os.path.join(project_directory, 'data', 'valve_check')
pl_deploy_directory = os.path.join(project_directory, 'data', 'pl_deploy')
battery_analysis_directory = os.path.join(project_directory, 'data', 'battery_analysis')
rf_performance_directory = os.path.join(project_directory, 'data', 'rf_performance_analysis')




def file_location_user_input() -> str:
    """
    Prompts the user to enter a file location until a valid path is provided.

    Returns:
    - str: The valid file location entered by the user.
    """

    while True:
        directory_location = input("input:" )

        if os.path.exists(directory_location):
            print(f"\n\n\nFile location found: {directory_location}.\n\n\n")
            # obtain basename
            directory_base_name = os.path.basename(directory_location)
            return directory_location, directory_base_name
        else:
            print("\n\nFile location does not exist. Please enter a valid location.\n\n")