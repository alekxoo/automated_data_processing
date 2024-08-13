import sys
import os
import openpyxl
import shutil
import pandas as pd
import nptdms
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QListWidget, QLabel, QMessageBox, QCheckBox, QDialog, QLineEdit, QComboBox,
                             QProgressBar, QDialogButtonBox)
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QTimer
from src.helper.file_handler import *
from src.processing.processing import *
import ctypes
import logging

from src.helper.file_handler import pre_processed_csv_directory

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class PreprocessTDMSDialog(QDialog):
    def __init__(self, parent=None):
        try:
            super().__init__(parent)
            self.setWindowTitle("Pre-process TDMS File")
            self.setModal(True)
            layout = QVBoxLayout()

            self.tm_events_checkbox = QCheckBox("Is there a TM Events File?")
            layout.addWidget(self.tm_events_checkbox)
            self.tm_events_checkbox.stateChanged.connect(self.toggle_tm_events_widgets)

            self.state7_time_input = QLineEdit()
            self.state7_time_label = QLabel("Enter time of state 7:")
            layout.addWidget(self.state7_time_label)
            layout.addWidget(self.state7_time_input)

            self.tm_events_file_path = QLineEdit()
            self.tm_events_file_button = QPushButton("Browse")
            self.tm_events_file_button.clicked.connect(self.browse_tm_events_file)

            tm_events_layout = QHBoxLayout()
            tm_events_layout.addWidget(QLabel("TM Events File:"))
            tm_events_layout.addWidget(self.tm_events_file_path)
            tm_events_layout.addWidget(self.tm_events_file_button)
            layout.addLayout(tm_events_layout)

            self.tdms_file_path = QLineEdit()
            self.tdms_file_button = QPushButton("Browse")
            self.tdms_file_button.clicked.connect(self.browse_tdms_file)

            tdms_layout = QHBoxLayout()
            tdms_layout.addWidget(QLabel("TDMS File:"))
            tdms_layout.addWidget(self.tdms_file_path)
            tdms_layout.addWidget(self.tdms_file_button)
            layout.addLayout(tdms_layout)

            self.sampling_frequency = QLineEdit()
            layout.addWidget(QLabel("Enter the sampling frequency of the TDMS file:"))
            layout.addWidget(self.sampling_frequency)

            self.test_type_combo = QComboBox()
            self.test_type_combo.addItems(["S1_ATP", "S2_ATP", "STATIC_FIRE", "WET_DRESS", "LAUNCH"])
            layout.addWidget(QLabel("Select Test Type:"))
            layout.addWidget(self.test_type_combo)

            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)
            layout.addWidget(self.button_box)

            self.setLayout(layout)
            self.toggle_tm_events_widgets()
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"An error occurred during dialog initialization: {str(e)}")
            logging.exception("Error during PreprocessTDMSDialog initialization")

    def toggle_tm_events_widgets(self):
        try:
            has_tm_events = self.tm_events_checkbox.isChecked()
            self.state7_time_label.setVisible(not has_tm_events)
            self.state7_time_input.setVisible(not has_tm_events)
            self.tm_events_file_path.setVisible(has_tm_events)
            self.tm_events_file_button.setVisible(has_tm_events)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error toggling TM events widgets: {str(e)}")
            logging.exception("Error in toggle_tm_events_widgets")

    def browse_tm_events_file(self):
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select TM Events File", "", "Text Files (*.txt)")
            if file_path:
                self.tm_events_file_path.setText(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error browsing TM events file: {str(e)}")
            logging.exception("Error in browse_tm_events_file")

    def browse_tdms_file(self):
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select TDMS File", "", "TDMS Files (*.tdms)")
            if file_path:
                self.tdms_file_path.setText(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error browsing TDMS file: {str(e)}")
            logging.exception("Error in browse_tdms_file")

    def get_inputs(self):
        try:
            return {
                "has_tm_events": self.tm_events_checkbox.isChecked(),
                "state7_time": self.state7_time_input.text(),
                "tm_events_file": self.tm_events_file_path.text(),
                "tdms_file": self.tdms_file_path.text(),
                "sampling_frequency": self.sampling_frequency.text(),
                "test_type": self.test_type_combo.currentText()
            }
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error getting inputs: {str(e)}")
            logging.exception("Error in get_inputs")
            return {}

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("Kootomation")
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kootomation_ico.ico')
            self.setWindowIcon(QtGui.QIcon(icon_path))

            if sys.platform == 'win32':
                myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            else:
                # Handle non-Windows platforms
                print("Running on a non-Windows platform")

            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QListWidget {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            self.setGeometry(100, 100, 600, 400)

            main_layout = QVBoxLayout()

            main_layout.addWidget(QLabel("Step 1: Pre-Process TDMS or Load Pre-Processed Parquet file:"))
            preprocess_button = QPushButton("Pre-process TDMS File")
            preprocess_button.clicked.connect(self.preprocess_tdms)
            main_layout.addWidget(preprocess_button)

            load_csv_button = QPushButton("Load Parquet File")
            load_csv_button.clicked.connect(self.load_csv)
            main_layout.addWidget(load_csv_button)

            main_layout.addWidget(QLabel("\nStep 2: Select Parameters for Data Processing"))

            add_config_button = QPushButton("Add Config File")
            add_config_button.clicked.connect(self.add_config_file)
            main_layout.addWidget(add_config_button)

            self.config_list = QListWidget()
            main_layout.addWidget(QLabel("Config Files:"))
            main_layout.addWidget(self.config_list)
            self.load_config_files()

            self.group_channel_checkbox = QCheckBox("Group Channels")
            self.group_channel_checkbox.setChecked(True)
            main_layout.addWidget(self.group_channel_checkbox)

            self.test_list = QListWidget()
            self.test_list.setSelectionMode(QListWidget.MultiSelection)
            main_layout.addWidget(QLabel("Tests:"))
            main_layout.addWidget(self.test_list)

            self.filter_points_input = QLineEdit()
            self.filter_points_input.setPlaceholderText("Enter number of data points to filter ")
            main_layout.addWidget(QLabel("Number of Data Points to Filter: (recommended: 1 HZ: 1, 25 HZ: 4, 100 HZ: 16)"))
            main_layout.addWidget(self.filter_points_input)

            process_button = QPushButton("Process Selected Tests")
            process_button.clicked.connect(self.process_tests)
            main_layout.addWidget(process_button)

            main_layout.addWidget(QLabel("\nReview Results:"))
            open_folder_button = QPushButton("Open Data Results Folder")
            open_folder_button.clicked.connect(self.open_data_folder)
            main_layout.addWidget(open_folder_button)

            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)

            self.pre_processed_file_path = None
            self.processed_tdms_df = None

        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"An error occurred during initialization: {str(e)}")
            logging.exception("Error during MainWindow initialization")

    def preprocess_tdms(self):
        try:
            dialog = PreprocessTDMSDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                QMessageBox.information(self, "Info", f"Pre-Processing TDMS & Saving as Parquet... (Press Ok to start)")
                QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                try:
                    inputs = dialog.get_inputs()
                    if inputs["has_tm_events"]:
                        state7_time_float = self.parse_for_state7_time_txt(inputs["tm_events_file"], dialog)
                    else:
                        state7_time_float = float(inputs["state7_time"])

                    tdms_parameter_list = self.load_tdms(inputs["tdms_file"], inputs["sampling_frequency"], dialog)
                    self.pre_processed_file_path = self.pre_process_tdms(tdms_parameter_list, state7_time_float,
                                                                         inputs["test_type"])
                finally:
                    QApplication.restoreOverrideCursor()
                    QMessageBox.information(self, "Info", "TDMS file pre-process complete.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during preprocessing: {str(e)}")
            logging.exception("Error during TDMS preprocessing")

    def parse_for_state7_time_txt(self, file_name, dialog):
        try:
            directory = os.path.dirname(dialog.tm_events_file_path.text())
            file_path = os.path.join(directory, file_name)

            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if 'State Machine State Change (1)' in line and 'ID 7' in line:
                        state7_time = float(line.split()[1])
                        print(f'Time when State Machine State Change (1) ID 7 occurred: {state7_time}')
                        return state7_time
            logging.warning(f"State 7 time not found in file: {file_path}")
            QMessageBox.warning(self, "Warning", "State 7 time not found in the file.")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error parsing state7 time from file: {str(e)}")
            logging.exception(f"Error parsing state7 time from file: {file_name}")
            raise

    def load_tdms(self, file_name, sampling_frequency, dialog):
        try:
            file_path = os.path.join(os.path.dirname(dialog.tdms_file_path.text()), file_name)
            tdms_file = nptdms.TdmsFile.read(file_path)
            return [(file_name, tdms_file, sampling_frequency)]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading TDMS file: {str(e)}")
            logging.exception(f"Error loading TDMS file: {file_name}")
            raise

    def pre_process_tdms(self, tdms_parameter_list, state7_time_float, test_type):
        try:
            file_name, tdms_file, sampling_frequency_str = tdms_parameter_list[0]

            print(f"Processing file: {file_name}")
            data = tdms_file.as_dataframe()
            print(f"DataFrame shape: {data.shape}")

            data.columns = data.columns.str.replace("'", "").str.split('/', n=2).str[2]

            print("Time Aligning Data")
            data["100-HZ-DATA FSW TIME"] -= state7_time_float
            print("Time Alignment Complete")

            if sampling_frequency_str == "1":
                print("1HZ Detected - Filtering Vehicle OFF")
                pcdu_cntr_rate_threshold = 20
                current_draw_threshold = 1

                if test_type == "S1_ATP":
                    pcdu_cntr_rate = "S1 PCDU CNTR RATE"
                    current_draw = "S1PS1 CURRENT ACT"
                else:  # S2_ATP
                    pcdu_cntr_rate = "S2 PCDU CNTR RATE"
                    current_draw = "S2PS1 CURRENT ACT"

                data = data[
                    (data[pcdu_cntr_rate] > pcdu_cntr_rate_threshold) | (data[current_draw] > current_draw_threshold)]
                print("Vehicle OFF data filtered")

            pre_processed_file_name = os.path.basename(file_name) + "_pre_processed.parquet"
            os.makedirs(pre_processed_csv_directory, exist_ok=True)
            pre_processed_file_path = os.path.join(pre_processed_csv_directory, pre_processed_file_name)

            print(f"Saving pre-processed data to: {pre_processed_file_path}")
            data.to_parquet(pre_processed_file_path, index=False)

            return pre_processed_file_path

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in pre-processing TDMS: {str(e)}")
            logging.exception("Error in pre_process_tdms")
            raise

    def load_csv(self):
        try:
            os.makedirs(pre_processed_csv_directory, exist_ok=True)
            self.pre_processed_file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Parquet File",
                pre_processed_csv_directory,
                "Parquet Files (*.parquet)"
            )
            if self.pre_processed_file_path:
                QMessageBox.information(self, "Info", "Parquet file loading process complete.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading Parquet file: {str(e)}")
            logging.exception("Error in load_csv")

    def load_config_files(self):
        try:
            config_xlsx_files = [file for file in os.listdir(config_directory) if file.endswith(".xlsx")]
            self.config_list.addItems(config_xlsx_files)
            self.config_list.itemClicked.connect(self.load_tests)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading config files: {str(e)}")
            logging.exception("Error in load_config_files")

    def load_tests(self, item):
        try:
            xlsx_file_path = os.path.join(config_directory, item.text())
            workbook = openpyxl.load_workbook(xlsx_file_path)
            self.test_list.clear()
            self.test_list.addItems(workbook.sheetnames)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading tests: {str(e)}")
            logging.exception("Error in load_tests")

    def process_tests(self):
        try:
            if not self.pre_processed_file_path:
                QMessageBox.warning(self, "Warning", "Please pre-process TDMS file or load CSV file first.")
                return

            selected_config = self.config_list.currentItem()
            if not selected_config:
                QMessageBox.warning(self, "Warning", "Please select a config file.")
                return

            selected_tests = self.test_list.selectedItems()
            if not selected_tests:
                QMessageBox.warning(self, "Warning", "Please select at least one test.")
                return

            if self.filter_points_input.text():
                try:
                    filter_points = int(self.filter_points_input.text())
                except ValueError:
                    QMessageBox.warning(self, "Warning", "Invalid filter points value.")

            xlsx_file_path = os.path.join(config_directory, selected_config.text())

            for test_item in selected_tests:
                selected_file_name = test_item.text()

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Info")
                msg_box.setText(f"Processing {selected_file_name}... (auto-closes in 2 seconds)")
                msg_box.setStandardButtons(QMessageBox.Ok)

                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(msg_box.close)
                timer.start(2000)

                result = msg_box.exec_()

                if result == QMessageBox.Ok or result == 0:
                    QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                    try:
                        print(f"\nWorking on {selected_file_name}...\n")
                        self.processed_tdms_df = pd.read_parquet(self.pre_processed_file_path)

                        selected_file_directory = os.path.join(data_directory, selected_file_name)
                        if os.path.exists(selected_file_directory):
                            shutil.rmtree(selected_file_directory)
                        os.makedirs(selected_file_directory)

                        config_df = pd.read_excel(xlsx_file_path, sheet_name=selected_file_name)
                        group_channel_bool = "1" if self.group_channel_checkbox.isChecked() else "0"
                        general_processing(selected_file_directory, self.processed_tdms_df, config_df,
                                           group_channel_bool, filter_points)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Error processing {selected_file_name}: {str(e)}")
                        logging.exception(f"Error processing {selected_file_name}")
                    finally:
                        QApplication.restoreOverrideCursor()

                    completion_msg = QMessageBox(self)
                    completion_msg.setWindowTitle("Info")
                    completion_msg.setText(
                        f"Processing Completed for {selected_file_name}... (auto-closes in 2 seconds)")
                    completion_msg.setStandardButtons(QMessageBox.Ok)

                    timer = QTimer(self)
                    timer.setSingleShot(True)
                    timer.timeout.connect(completion_msg.close)
                    timer.start(2000)

                    completion_msg.exec_()

            final_msg = QMessageBox(self)
            final_msg.setWindowTitle("Info")
            final_msg.setText("All Processing Completed.")
            final_msg.setStandardButtons(QMessageBox.Ok)

            final_msg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during test processing: {str(e)}")
            logging.exception("Error in process_tests")

    def open_data_folder(self):
        try:
            if os.path.exists(data_directory):
                if sys.platform == 'win32':
                    os.startfile(data_directory)
            else:
                QMessageBox.warning(self, "Warning", "Data directory does not exist.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening data folder: {str(e)}")
            logging.exception("Error in open_data_folder")

    def add_config_file(self):
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select Config File", "", "Excel Files (*.xlsx)")
            if file_path:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(config_directory, file_name)

                if os.path.exists(destination_path):
                    overwrite = QMessageBox.question(self, "File Exists",
                                                     "A file with this name already exists in the config directory. Overwrite?",
                                                     QMessageBox.Yes | QMessageBox.No)
                    if overwrite == QMessageBox.No:
                        return
                try:
                    shutil.copy(file_path, destination_path)
                    self.config_list.addItem(file_name)
                    QMessageBox.information(self, "Success", f"Config file '{file_name}' added successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add config file: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding config file: {str(e)}")
            logging.exception("Error in add_config_file")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("An unexpected error occurred.")
        error_dialog.setInformativeText(str(e))
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()
        logging.exception("Unexpected error occurred:")
        sys.exit(1)