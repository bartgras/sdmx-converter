"""
Parse a Canadian Census XML document (in SDMX format) and yield a CSV with the
same data. The data will be Tidy (http://vita.had.co.nz/papers/tidy-data.pdf).

However, all the column names and concept values will remain as they appear in
the SDMX file -- which is to say, not very human-readable. See the other scripts
in this folder to build human-readable CSV files.
"""

import xml.etree.cElementTree as cElementTree
import csv
import argparse
from collections import OrderedDict

PARSER = argparse.ArgumentParser(description='Process an SDMX file to CSV.')
PARSER.add_argument('input_file', type=argparse.FileType('r'),
                    help='a Census Canada SDMX data file')

ARGS = PARSER.parse_args()

INPUT_FILE = ARGS.input_file
OUTPUT_FILE_NAME = INPUT_FILE.name.replace('.xml', '.csv')

ORDERED_KEY_DICT = OrderedDict()

def remove_xml_namespace(tag_name):
    """
    Remove a namespace from a tag, e.g., "{www.plotandscatter.com}TagName" will
    be returned as "TagName"
    """
    if '}' in tag_name:
        tag_name = tag_name.split('}', 1)[1]
    return tag_name


def append_row(row_array, row, value):
    """ Append a row to the row_array. """
    row['OBS_VALUE'] = value
    row_array.append(row)
    print(row)


def build_rows(row_array):
    """
    Iteratively parse the SDMX file, storing the concept-value pairs and the
    observed value in a dictionary.
    """
    row = {}
    print(INPUT_FILE)
    with ARGS.input_file as input_file:
        for _, elem in cElementTree.iterparse(input_file):
            tag_name = remove_xml_namespace(elem.tag)
            if tag_name == 'Value':
                attribute_name = elem.attrib['concept']
                attribute_value = elem.attrib['value']
                row[attribute_name] = attribute_value
                ORDERED_KEY_DICT[attribute_name] = 1
                if attribute_name == 'OBS_STATUS':
                    # In this case, we are actually finished with this row, and
                    # there is no valid value reported (it has been suppressed).
                    append_row(row_array, row, None)
                    row = {}
            if tag_name == 'ObsValue':
                append_row(row_array, row, elem.attrib['value'])
                row = {}
            elem.clear()


def write_rows(row_array):
    """ Write the rows to a CSV file. """
    ORDERED_KEY_DICT['OBS_VALUE'] = 1
    with open(OUTPUT_FILE_NAME, 'w') as output_file:
        dict_writer = csv.DictWriter(
            output_file, fieldnames=list(ORDERED_KEY_DICT.keys()))
        dict_writer.writeheader()
        dict_writer.writerows(row_array)


ROWS = []
print("Building rows...")
build_rows(ROWS)
print("Writing to CSV...")
write_rows(ROWS)
print("Done.")
