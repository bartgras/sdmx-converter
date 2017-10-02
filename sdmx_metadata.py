"""
Loads and parses the Structure SDMX file at the given path.
"""

import pprint
import xml.etree.cElementTree as cElementTree

class SDMXMetadata:
    """
    Represents the metadata, including variable codes, names associated with those
    variable codes, and variable value lists, for an SDMX file. Loaded from a
    standardized SDMX Structure file.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, sdmx_structure_file_path):
        self.__root = self.__load_xml(sdmx_structure_file_path)
        self.__load_primary_measure()
        self.__load_concepts()
        self.__load_code_levels()

    @staticmethod
    def __remove_xml_namespace(tag_name):
        """
        Remove a namespace from a tag, e.g., "{www.plotandscatter.com}TagName" will
        be returned as "TagName"
        """
        if '}' in tag_name:
            tag_name = tag_name.split('}', 1)[1]
        return tag_name

    def __load_xml(self, sdmx_structure_file_path):
        """
        NB. Strips the namespaces!
        """
        iterator = cElementTree.iterparse(sdmx_structure_file_path)
        for _, element in iterator:
            element.tag = self.__remove_xml_namespace(element.tag)
        return iterator.root

    def __load_primary_measure(self):
        """
        Load the primary measure, which with our datasets will usually be
        OBS_VALUE.
        """
        code = self.__root.find('.//PrimaryMeasure').attrib['conceptRef']
        self.__primary_measure_code = code

    def __load_concepts(self):
        """
        Load the concepts (variables) for this SDMX file. Also build maps that
        permit going from concept code to name, or name to concept code.
        """
        self.__concept_codes = []
        self.__concept_codelist_keys = []
        self.__concept_code_to_codelist_key = {}
        self.__codelist_key_to_concept_code = {}
        self.__concept_code_to_name = {}
        self.__name_to_concept_code = {}

        # First, find the concepts in the KeyFamily
        for concept in self.__root.findall('.//KeyFamily//*[@conceptRef]'):
            code = concept.attrib['conceptRef']
            self.__concept_codes.append(code)
            if 'codelist' in concept.attrib:
                codelist_key = concept.attrib['codelist']
                self.__concept_codelist_keys.append(codelist_key)
                self.__concept_code_to_codelist_key[code] = codelist_key
                self.__codelist_key_to_concept_code[codelist_key] = code

        # Next, find the concept names
        for code in self.__concept_codes:
            name = self.__root.find('.//Concept[@id="%s"]' % code).find('Name').text
            self.__concept_code_to_name[code] = name
            self.__name_to_concept_code[name] = code

        pprint.pprint(self.__concept_codes)
        pprint.pprint(self.__concept_code_to_name)

    def __load_code_levels(self):
        """
        Load the concept code lists (mapping variable numbers, e.g. 1, 2, and 3
        for Sex, to their names, e.g. Total, Male, Female).
        """
        self.__code_levels = {}

        for codelist_key in self.__concept_codelist_keys:
            print('>>> codelist_key', codelist_key)
            code_list = self.__root.find('.//CodeList[@id="%s"]' % codelist_key)
            if code_list:  # Sometimes there are codes without code lists.

                # When storing the code lists, we actually want to store them
                # in a dict with a key of concept code, not CL_CONCEPT_CODE.
                # So, get the original concept code.
                concept_code = self.__codelist_key_to_concept_code[codelist_key]
                self.__code_levels[concept_code] = {}

                for level in code_list.findall('Code'):
                    code_value = level.attrib['value']
                    code_description = level.find('Description').text
                    self.__code_levels[concept_code][code_value] = code_description

        pprint.pprint(self.__code_levels)

    def is_primary_measure_code(self, code):
        """ Is this the primary measure code? """
        return code == self.__primary_measure_code

    def codes(self):
        """ Load the concept codes. """
        return self.__concept_codes

    def name_by_code(self, code):
        """ Get a variable name given a code. """
        name = self.__concept_code_to_name[code]

        return name

    def code_by_name(self, name):
        """ Get a code given a variable name. """
        return self.__name_to_concept_code[name]

    def code_levels(self):
        """ Get the set of all code levels, for all codes. """
        return self.__code_levels

    def code_levels_by_code(self, code):
        """ Get the set of code levels for a given concept code. """
        if self.is_primary_measure_code(code):
            return None
        return self.__code_levels[code]

    def description_by_code_level(self, code, code_level, trim=False):
        """
        Get the description for a given code level. Note that if the code is the
        primary measure code, i.e. the code_level passed in is the observation
        value, the code_level itself (i.e. observation value) will be returned.
        Optionally, trim the name string (some census names are indented with
        spaces, e.g. '    75 years and over').
        """
        if not code_level:
            return code_level
        if self.is_primary_measure_code(code):
            return code_level
        description = self.__code_levels[code][code_level]
        if trim:
            description = description.strip()
        return description
