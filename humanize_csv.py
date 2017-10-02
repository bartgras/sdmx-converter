"""
Load a CSV file that was generated from a Canadian Census XML document (in SDMX
format) via the sdmx_to_csv.py and yield a CSV with the same data, but made
human-readable: the numerical code levels replaced with their code descriptions
(e.g. 1, 2, 3 will be Total, Male, Female).

This script requires that the input file conform to a naming standard:
Generic_CATALOG-NUM.csv, where CATALOG-NUM is a valid catalogue number (e.g.
98-400-X2016110).

The script also requires that the SDMX XML structure file be in the same
directory as the CSV; it must be named Structure_CATALOG-NUM.xml.

The data will still be Tidy (http://vita.had.co.nz/papers/tidy-data.pdf).

Note that the resulting data file will likely be significantly larger than the
input file.
"""

import csv
import argparse
import re
from sdmx_metadata import SDMXMetadata

PARSER = argparse.ArgumentParser(
    description='Humanize a CSV file by filling in its values.')
PARSER.add_argument('input_file',
                    type=argparse.FileType('r'),
                    help='a CSV file generated from an SDMX data file')

ARGS = PARSER.parse_args()
INPUT_FILE = ARGS.input_file

GEOGRAPHY_CODE = 'Geography code'

def initialize():
    """
    Given the input file passed in to the script, parse its name and generate
    the appropriate structure and output file names.
    """

    catalog_extractor = re.compile(r'.*/Generic_(.*)\.csv')
    try:
        catalog_num = catalog_extractor.findall(INPUT_FILE.name)[0]
    except IndexError:
        raise LookupError(
            'Could not find catalogue number. '
            'The file name must be of the pattern "Generic_CATALOG-NUM.csv".'
        )

    print(catalog_num)

    structure_file_name = INPUT_FILE.name \
                                    .replace('Generic', 'Structure') \
                                    .replace('csv', 'xml')

    print(structure_file_name)

    output_file_name = INPUT_FILE.name.replace('.csv', '.humanized.csv')

    return (structure_file_name, output_file_name)


def rebuild_csv(sdmx_metadata, input_file, output_file_name):
    """
    Generate the new CSV, with the humanized column titles and values.
    """

    dict_reader = csv.DictReader(input_file)

    # First, transform fieldnames
    fieldnames = [
        sdmx_metadata.name_by_code(x)
        for x in list(dict_reader.fieldnames)
    ]
    fieldnames.insert(0, GEOGRAPHY_CODE)

    # Now, iterate through the input file, transform using a dictionary
    # comprehension, and write to the output file.
    with open(output_file_name, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        dict_writer.writeheader()

        for line in dict_reader:
            new_line = {
                sdmx_metadata.name_by_code(k):
                sdmx_metadata.description_by_code_level(k, v)
                for k, v in line.items()
            }
            # Retain the geography code
            if 'GEO' in line:
                new_line[GEOGRAPHY_CODE] = line['GEO']
            print(new_line)
            dict_writer.writerow(new_line)


STRUCTURE_FILE_NAME, OUTPUT_FILE_NAME = initialize()
SDMX_METADATA = SDMXMetadata(STRUCTURE_FILE_NAME)
rebuild_csv(SDMX_METADATA, INPUT_FILE, OUTPUT_FILE_NAME)
