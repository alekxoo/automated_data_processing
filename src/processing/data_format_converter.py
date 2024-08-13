def tdms_to_df(tdms_file):
    data = tdms_file.as_dataframe()
    data.columns = data.columns.str.replace("'", "").str.split('/', n=2).str[2]

def df_to_csv():
    print()