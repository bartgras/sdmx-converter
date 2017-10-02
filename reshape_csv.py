"""
Given a CSV file that is in tall or "Tidy" format, reshape it into a file that
is "wide," optionally providing a subset of columns to include in the wide file.
Reshaping in this way is primarily for the purpose of saving disk space, and for
some libraries which expect wide data; for most data analysis, especially in
pandas or R, data should be put back into the Tidy format.
"""

import pandas
import numpy
import csv
import argparse

PARSER = argparse.ArgumentParser(
    description='Reshape a CSV file from tall (Tidy) to wide format')
PARSER.add_argument('input_file',
                    type=argparse.FileType('r'),
                    help='a CSV file to reshape')

ARGS = PARSER.parse_args()
INPUT_FILE = ARGS.input_file

OUTPUT_FILE_NAME = INPUT_FILE.name.replace('.csv', '.pivoted.csv')

def rename_column(column):
    column = str(column).strip().lower()
    column = column.replace(' ($)', '')
    column = column.replace('$', '')
    column = column.replace('total - ', 'all-')
    column = column.replace(' ', '-')
    column = column.replace(',', '')
    return column


def load_data():
    data = pandas.read_csv(INPUT_FILE)

    # Remove 2005 data, if applicable
    # if 'Year (2)' in data:
    #     data = data[(data['Year (2)'] == 2015)]
    #     data = data.drop('Year (2)', 1)

    # Drop observation missing status if it's there
    if 'Observation missing status' in data:
        data = data.drop('Observation missing status', 1)

    # Convert the first column to string, so it sorts better
    data.ix[:, 0] = data.ix[:, 0].apply(str)

    # Trim the whitespace in the second column
    data.ix[:, 1] = data.ix[:, 1].map(str.strip)

    print(data.head())

    return data

def pivot_data(data):
    # We assume the first item in the list is the index, and the last is the value.
    # All the ones in the middle are the pivot columns.
    all_columns = list(data)
    index_columns = all_columns[0:2]
    pivot_columns = all_columns[2:-1]
    value_column = all_columns[-1]

    # Build the pivot table
    pivoted = data.pivot_table(
        index=index_columns, columns=pivot_columns, values=value_column)

    pivoted.columns = ['_'.join(col).strip() for col in [
        tuple(rename_column(column) for column in column_list)
        for column_list in pivoted.columns.values
    ]]

    # Rename the index columns
    pivoted.index.names = [rename_column(column) for column in pivoted.index.names]

    # Sort by the index columns
    pivoted = pivoted.sort_index()

    return pivoted

def to_csv(data):
    data.to_csv(OUTPUT_FILE_NAME)

DATA = load_data()
PIVOTED_DATA = pivot_data(DATA)
to_csv(PIVOTED_DATA)