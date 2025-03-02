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

# FASTAPI dependencies
from typing import Union                                                        
from enum import Enum                                                           
from fastapi import FastAPI, status, HTTPException, File, UploadFile
from pydantic import BaseModel

import argparse  ### DO I NEED THIS AFTER IT IS CONVERTED to FASTAPI?
import os
import sys
import json
from typing import Dict, Any
from pathlib import Path
import logging
import uuid
from datetime import datetime


# pypdf dependencies
from pypdf import PdfReader, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

description = """

Open Tax Liberty is a FastAPI application that will take as input a json
configuration file then produce tax forms filled out for the user.
                                                                                
""" 

tags_metadata = [                                                               
    {                                                                           
        "name": "system",                                                       
        "description": "Queries the system and prints specs for  GPUs and versions of libraries",
    },                                                                          
    {                                                                           
        "name": "models",                                                       
        "description": "Manage models. So _fancy_ they have their own docs.",   
        "externalDocs": {                                                       
            "description": "models external docs",                              
            "url": "https://fastapi.tiangolo.com/",                             
        },                                                                      
    },                                                                          
]

app = FastAPI(                                                                  
    title="Open Tax Liberty",                                                 
    description=description,                                                    
    summary="Open Tax Liberty.",      
    version="0.0.1",                                                            
    #terms_of_service="http://example.com/terms/",                              
    contact={                                                                   
        "name": "Todd V. Rovito",                                               
        "url": "https://github.com/qualia-insights/opentaxliberty",                                                
        "email": "rovitotv@gmail.com",                                          
    },                                                                          
    license_info={                                                              
        "name": "AGPLv3",                                                       
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",                 
    },                                                                          
    openapi_tags = tags_metadata,                                               
)  

# configuration ===============================================================  
UPLOAD_DIR = "/home/rovitotv/temp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

def parse_and_validate_input_json(input_json_file_name: str, 
        pdf_template_file_name: str, job_dir: str) -> Dict[str, Any]:
    try:
        # check template
        template_file_path = Path(pdf_template_file_name)
        if template_file_path.exists() == False:
            error_str = (f"Error: configuration:template_1040_pdf does not exist: {template_file_path}")
            logging.error(error_str)
            raise FileNotFoundError(error_str)
    
        with open(input_json_file_name, 'r') as f:
            data = json.load(f)  # Load the JSON data from the file
            return data
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {input_json_file_name}")
        sys.exit(4)
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred: {e}")
        sys.exit(4)

@app.post("/api/process-tax-form", status_code=status.HTTP_201_CREATED)
async def process_tax_form(
    config_file: UploadFile = File(...),
    pdf_form: UploadFile = File(...),
):
    """
    Process a tax form PDF using a JSON configuration file.
    
    Args:
        config_file (UploadFile): JSON configuration file that defines how to process the form
        pdf_form (UploadFile): The PDF tax form to process
    
    Returns:
        ProcessingResult: Results of the form processing
    """
    # Generate unique ID for this processing request
    form_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create directories for this processing job
    job_dir = os.path.join(UPLOAD_DIR, form_id)
    os.makedirs(job_dir, exist_ok=True)
    
    try:
        # Save json configuration file
        config_path = os.path.join(job_dir, f"config_{config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())
            
        # Save PDF file
        pdf_path = os.path.join(job_dir, f"form_{pdf_form.filename}")
        with open(pdf_path, "wb") as f:
            f.write(await pdf_form.read())

        json_dict = parse_and_validate_input_json(config_path, pdf_path, job_dir)

        return 200

    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing form: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

'''
# this is the original program before it was a fastapi application
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
'''
