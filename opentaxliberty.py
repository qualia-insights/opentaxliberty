# Open Tax Liberty - Python program to make IRS 1040 forms
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
#  OpenTaxLiberty for tax year 2024 
import argparse
import os
import sys
import json
from typing import Dict, Any
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes

def write_field_pdf(field_name, field_value):
    writer.update_page_form_field_values(
        writer.pages[0],
        #{"f1_32[0]": "11.11"},
        {field_name: field_value},
        auto_regenerate = False,
    )

def get_widgets():
    fields = []
    for page in reader.pages:
        for annot in page.annotations:
            annot = annot.get_object()
            if annot[AnnotationDictionaryAttributes.Subtype] == "/Widget":
                fields.append(annot)
    return fields
    
def fill_header():
    write_field_pdf("f1_04[0]", "Bob P")
    write_field_pdf("f1_05[0]", "Smith")
    write_field_pdf("f1_06[0]", "222         22         2222")
    write_field_pdf("f1_10[0]", "9370 Liberty Court")
    write_field_pdf("f1_12[0]", "Dayton")
    write_field_pdf("f1_13[0]", "OH")
    write_field_pdf("f1_13[0]", "45468")
    write_field_pdf("c1_3[0]", "/1")   # filing Status = Single
    #write_field_pdf("c1_5[0]", "/1")   # digital assets
    write_field_pdf("c1_6[0]", "/1")   # someone can claim you as a dependent

def process_input_json(input_json_data: Dict[str, Any]):
    for key in input_json_data:
        if key == "configuration":
            continue
        elif key == "w-2":
            w2_data = input_json_data[key]
            total_box_1 = 0
            for index in range(0, len(w2_data)-1):
                total_box_1 += w2_data[index]['box_1']
            write_field_pdf(w2_data[-1]['tag'], total_box_1)
            continue
        elif key == "ssn":
            ssn_string = input_json_data[key]['value']
            ssns = ssn_string.split("-")
            ssn_output = ("%s         %s         %s" % (ssns[0], ssns[1], ssns[2]))
            write_field_pdf(input_json_data[key]['tag'], ssn_output)
        else:
            write_field_pdf(input_json_data[key]['tag'], input_json_data[key]['value'])

def check_arguments(input_json_file_name: str):
    input_json_path = Path(input_json_file_name)
    if input_json_path.exists() == False:
        print(f"Error: input_json argument does not exist: {input_json_path}", file=sys.stderr)
        sys.exit(3)

def parse_and_validate_input_json(input_json_file_name: str) -> Dict[str, Any]:
    try:
        with open(input_json_file_name, 'r') as f:
            data = json.load(f)  # Load the JSON data from the file
            # check template
            template_file_path = Path(data['configuration']['template_1040_pdf'])
            if template_file_path.exists() == False:
                print(f"Error: configuration:template_1040_pdf does not exist: {template_file_path}", file=sys.stderr)
                sys.exit(3)
            # check output file path existence
            output_file_name_path = Path(data['configuration']['output_file_name'])
            output_path = output_file_name_path.parent
            if output_path.is_dir() == False:                                 
                print(f"Error: configuration:output_file_name parent is _NOT_ a directory: {output_path}", file=sys.stderr)
                sys.exit(3) 

            return data
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {input_json_file_name}")
        sys.exit(4)
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred: {e}")
        sys.exit(4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()                                          
    parser.add_argument("input_json", help="input file in json format to process")
    args = parser.parse_args()    
    check_arguments(args.input_json)
    input_json_data = parse_and_validate_input_json(args.input_json)

    reader = PdfReader(input_json_data["configuration"]["template_1040_pdf"])
    writer = PdfWriter()

    page = reader.pages[0]
    #fields = reader.get_form_text_fields()
    fields = reader.get_fields()
    keys_list = list(fields.keys())
    fields_widgets = get_widgets()
    #print(fields)
    writer.append(reader)
    process_input_json(input_json_data)
    #fill_header()

    with open(input_json_data["configuration"]["output_file_name"], "wb") as output_stream:
        writer.write(output_stream)
