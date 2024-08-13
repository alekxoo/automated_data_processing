import pandas as pd
import glob
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import os
import textwrap

def create_pdf_from_pngs(location_directory, output_filename):
    # Search for PNG files in the directory
    png_files = glob.glob(location_directory + '/**/*.png', recursive=True)
    xlsx_files = glob.glob(location_directory + '/*.xlsx')
    # Create a PDF file to save the PNGs
    max_rows_per_page = 20
    max_filename_length = 50

    with PdfPages(output_filename) as pdf:
        for xlsx_file in xlsx_files:
            df = pd.read_excel(xlsx_file)
            num_rows = len(df)
            num_pages = (num_rows - 1) // max_rows_per_page + 1  # Calculate number of pages

            for page_num in range(num_pages):
                start_idx = page_num * max_rows_per_page
                end_idx = min((page_num + 1) * max_rows_per_page, num_rows)
                page_df = df.iloc[start_idx:end_idx]

                # Create a table-like representation of the CSV data using matplotlib
                fig, ax = plt.subplots(figsize=(10, 6))  # Adjust figsize as needed
                ax.axis('off')  # Hide axes
                ax.table(cellText=page_df.values, colLabels=page_df.columns, loc='center')
                ax.set_title(f'Results Summary (Page {page_num + 1}/{num_pages})', fontsize=16)
                pdf.savefig(fig)  # Save the figure (including the table) to the PDF
                plt.close(fig)  # Close the figure
        # Iterate through the PNG files
        previous_directory = None
        # Iterate through the PNG files
        for png_file in png_files:
            # Get the directory name
            directory_name = os.path.dirname(png_file).split(os.path.sep)[-1]
            # Check if this is the first PNG of a new directory
            if directory_name != previous_directory:
                # Add directory name as the first page
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.axis('off')  # Hide axes
                ax.text(0.5, 0.5, f'Category: {directory_name}', horizontalalignment='center',
                        verticalalignment='center', fontsize=16)
                pdf.savefig(fig)  # Save the figure to the PDF as the first page
                plt.close(fig)  # Close the figure
                previous_directory = directory_name

            # Read the PNG image and append it to the PDF
            image = plt.imread(png_file)
            filename_without_extension = os.path.splitext(os.path.basename(png_file))[0]

            wrapped_filename = textwrap.fill(filename_without_extension, width=max_filename_length)

            fig, ax = plt.subplots(figsize=(8, 6))
            ax.imshow(image)
            ax.axis('off')  # Hide axes

            # Adjust the vertical position based on the number of lines
            num_lines = len(wrapped_filename.split('\n'))
            y_pos = 1.05 + 0.03 * (num_lines - 1)  # Adjust 0.03 as needed for spacing

            ax.text(0.5, y_pos, wrapped_filename, horizontalalignment='center', verticalalignment='top',
                    transform=ax.transAxes, fontsize=12, wrap=True)

            pdf.savefig(fig)  # Save current figure to PDF
            plt.close(fig)  # Close current figure